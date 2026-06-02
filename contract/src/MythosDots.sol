// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "erc721a/contracts/ERC721A.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/common/ERC2981.sol";
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

interface IAggregatorV3 {
    function decimals() external view returns (uint8);
    function latestRoundData() external view returns (
        uint80 roundId, int256 answer, uint256 startedAt, uint256 updatedAt, uint80 answeredInRound
    );
}

/// @title Mythos Dots — degen pass-gated mint, trả ETH (quy đổi từ giá USD qua Chainlink)
/// @notice Agent ký EIP-712 pass {wallet,quota,nonce,deadline}. Pay-at-lock: giải đúng →
///         mint full quota + trả ETH ngay (oracle quy đổi từ giá USD phân tầng), hoàn dust.
contract MythosDots is ERC721A, ERC2981, Ownable, EIP712 {
    using ECDSA for bytes32;

    uint256 public constant MAX_PER_WALLET = 10;

    // ── Giá USD phân tầng theo thứ tự mint (6 decimals: 30000 = $0.03) ──
    uint256 public constant P1_END = 777;
    uint256 public constant P2_END = 3111;
    uint256 public constant P3_END = 5444;
    uint256 public constant PRICE1 = 30000;   // $0.03
    uint256 public constant PRICE2 = 150000;  // $0.15
    uint256 public constant PRICE3 = 250000;  // $0.25
    uint256 public constant PRICE4 = 350000;  // $0.35

    uint256 public immutable maxSupply;
    IAggregatorV3 public immutable priceFeed; // Chainlink ETH/USD
    uint256 public immutable feedUnit;        // 10**feed.decimals()
    uint256 public maxOracleAge = 3600;       // chấp nhận answer cũ tối đa (giây); 0 = bỏ qua

    bool public saleActive;
    string private _baseTokenURI;

    mapping(address => bool) public isAgentSigner;
    mapping(uint256 => bool) public usedNonce;
    mapping(address => uint256) public mintedOf;

    bytes32 private constant PASS_TYPEHASH =
        keccak256("Pass(address wallet,uint256 quota,uint256 nonce,uint256 deadline)");

    event Minted(address indexed wallet, uint256 quota, uint256 nonce, uint256 paidWei);

    constructor(
        uint256 _maxSupply,
        address _priceFeed,
        address _agentSigner,
        string memory baseURI,
        address royaltyReceiver
    ) ERC721A("Mythos Dots", "MYTHDOT") Ownable(msg.sender) EIP712("MythosDots", "1") {
        maxSupply = _maxSupply;
        priceFeed = IAggregatorV3(_priceFeed);
        feedUnit = 10 ** IAggregatorV3(_priceFeed).decimals();
        isAgentSigner[_agentSigner] = true;
        _baseTokenURI = baseURI;
        _setDefaultRoyalty(royaltyReceiver, 100); // 1%
    }

    // ───────────────────── Giá USD phân tầng ─────────────────────
    function priceAtIndex(uint256 idx) public pure returns (uint256) {
        if (idx <= P1_END) return PRICE1;
        if (idx <= P2_END) return PRICE2;
        if (idx <= P3_END) return PRICE3;
        return PRICE4;
    }

    /// @notice Tổng giá USD (6dp) cho `amount` token kế tiếp khi đã mint `startMinted` cái.
    function costForUsd(uint256 startMinted, uint256 amount) public pure returns (uint256 c) {
        for (uint256 i = 1; i <= amount; i++) c += priceAtIndex(startMinted + i);
    }

    /// @notice Giá ETH/USD hiện tại từ oracle (đã kiểm tra hợp lệ).
    function ethUsd() public view returns (uint256) {
        (, int256 answer,, uint256 updatedAt,) = priceFeed.latestRoundData();
        require(answer > 0, "oracle answer");
        if (maxOracleAge != 0) require(block.timestamp - updatedAt <= maxOracleAge, "oracle stale");
        return uint256(answer);
    }

    /// @notice Quy đổi USD(6dp) → wei ETH theo oracle.
    function usdToEth(uint256 usd6) public view returns (uint256) {
        return (usd6 * feedUnit * 1e18) / (1e6 * ethUsd());
    }

    /// @notice Tổng giá ETH (wei) cho `amount` token kế tiếp.
    function costForEth(uint256 startMinted, uint256 amount) public view returns (uint256) {
        return usdToEth(costForUsd(startMinted, amount));
    }

    /// @notice Giá ETH (wei) của token kế tiếp (cho UI).
    function currentPriceEth() external view returns (uint256) {
        return usdToEth(priceAtIndex(_totalMinted() + 1));
    }

    // ───────────────────────────── Mint ─────────────────────────────
    function passDigest(address wallet, uint256 quota, uint256 nonce, uint256 deadline)
        public view returns (bytes32)
    {
        return _hashTypedDataV4(keccak256(abi.encode(PASS_TYPEHASH, wallet, quota, nonce, deadline)));
    }

    function _consume(uint256 quota, uint256 nonce, uint256 deadline, bytes calldata sig) internal {
        require(saleActive, "sale off");
        require(block.timestamp <= deadline, "pass expired");
        require(!usedNonce[nonce], "nonce used");
        require(quota > 0 && quota <= MAX_PER_WALLET, "bad quota");
        address signer = passDigest(msg.sender, quota, nonce, deadline).recover(sig);
        require(isAgentSigner[signer], "bad signer");
        require(mintedOf[msg.sender] + quota <= MAX_PER_WALLET, "wallet cap");
        require(_totalMinted() + quota <= maxSupply, "sold out");
        usedNonce[nonce] = true;
        mintedOf[msg.sender] += quota;
    }

    /// @notice Pay-at-lock: mint đúng `quota`, trả ETH = costForEth(...), hoàn phần dư.
    function mintWithPass(uint256 quota, uint256 nonce, uint256 deadline, bytes calldata sig)
        external payable
    {
        uint256 cost = costForEth(_totalMinted(), quota);
        require(msg.value >= cost, "insufficient ETH");
        _consume(quota, nonce, deadline, sig);
        _mint(msg.sender, quota);
        emit Minted(msg.sender, quota, nonce, cost);
        uint256 refund = msg.value - cost;
        if (refund > 0) {
            (bool ok, ) = payable(msg.sender).call{value: refund}("");
            require(ok, "refund fail");
        }
    }

    // ───────────────────────────── Admin ─────────────────────────────
    function setSaleActive(bool s) external onlyOwner { saleActive = s; }
    function setAgentSigner(address a, bool ok) external onlyOwner { isAgentSigner[a] = ok; }
    function setMaxOracleAge(uint256 s) external onlyOwner { maxOracleAge = s; }
    function setRoyalty(address r, uint96 bps) external onlyOwner { _setDefaultRoyalty(r, bps); }
    function setBaseURI(string calldata uri) external onlyOwner { _baseTokenURI = uri; }

    function withdraw(address to) external onlyOwner {
        (bool ok, ) = payable(to).call{value: address(this).balance}("");
        require(ok, "withdraw fail");
    }

    // ───────────────────────────── Metadata ─────────────────────────────
    function _startTokenId() internal pure override returns (uint256) { return 1; }
    function _baseURI() internal view override returns (string memory) { return _baseTokenURI; }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        if (!_exists(tokenId)) revert URIQueryForNonexistentToken();
        string memory base = _baseURI();
        return bytes(base).length != 0
            ? string(abi.encodePacked(base, _toString(tokenId), ".json")) : "";
    }

    function supportsInterface(bytes4 id)
        public view override(ERC721A, ERC2981) returns (bool)
    {
        return ERC721A.supportsInterface(id) || ERC2981.supportsInterface(id);
    }
}
