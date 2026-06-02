// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Test.sol";
import "../src/MythosDots.sol";

contract MockFeed is IAggregatorV3 {
    int256 public answer;
    constructor(int256 a) { answer = a; }
    function decimals() external pure returns (uint8) { return 8; }
    function set(int256 a) external { answer = a; }
    function latestRoundData() external view returns (uint80, int256, uint256, uint256, uint80) {
        return (1, answer, block.timestamp, block.timestamp, 1);
    }
}

contract MythosDotsTest is Test {
    MythosDots nft;
    MockFeed feed;
    uint256 constant MAXS = 100;

    uint256 agentPk = 0xA11CE;
    address agent;
    address user = address(0xBEEF);

    function setUp() public {
        agent = vm.addr(agentPk);
        feed = new MockFeed(2000e8); // $2000 / ETH
        nft = new MythosDots(MAXS, address(feed), agent, "ipfs://CID/", address(this));
        nft.setSaleActive(true);
        vm.deal(user, 100 ether);
    }

    function _pass(address w, uint256 quota, uint256 nonce, uint256 deadline)
        internal view returns (bytes memory)
    {
        bytes32 d = nft.passDigest(w, quota, nonce, deadline);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(agentPk, d);
        return abi.encodePacked(r, s, v);
    }

    function test_MintWithPassEth() public {
        uint256 cost = nft.costForEth(0, 5);
        assertEq(cost, uint256(30000) * 5 * 1e20 / 2000e8); // sanity
        bytes memory sig = _pass(user, 5, 1, block.timestamp + 100);
        vm.prank(user);
        nft.mintWithPass{value: cost}(5, 1, block.timestamp + 100, sig);
        assertEq(nft.balanceOf(user), 5);
        assertEq(nft.ownerOf(1), user);
        assertEq(address(nft).balance, cost);
    }

    function test_RefundDust() public {
        uint256 cost = nft.costForEth(0, 3);
        bytes memory sig = _pass(user, 3, 1, block.timestamp + 100);
        uint256 before = user.balance;
        vm.prank(user);
        nft.mintWithPass{value: cost + 1 ether}(3, 1, block.timestamp + 100, sig);
        assertEq(user.balance, before - cost);       // chỉ trừ đúng cost, hoàn 1 ether
        assertEq(address(nft).balance, cost);
    }

    function test_RevertInsufficientEth() public {
        uint256 cost = nft.costForEth(0, 2);
        bytes memory sig = _pass(user, 2, 1, block.timestamp + 100);
        vm.prank(user);
        vm.expectRevert("insufficient ETH");
        nft.mintWithPass{value: cost - 1}(2, 1, block.timestamp + 100, sig);
    }

    function test_OracleConversion() public {
        // $0.03 @ $2000/ETH = 0.000015 ETH
        assertEq(nft.usdToEth(30000), 15e12);
        feed.set(3000e8); // $3000/ETH → rẻ hơn theo ETH
        assertEq(nft.usdToEth(30000), 1e13); // 0.00001 ETH
    }

    function test_TokenURI() public {
        uint256 cost = nft.costForEth(0, 1);
        bytes memory sig = _pass(user, 1, 1, block.timestamp + 100);
        vm.prank(user);
        nft.mintWithPass{value: cost}(1, 1, block.timestamp + 100, sig);
        assertEq(nft.tokenURI(1), "ipfs://CID/1.json");
    }

    function test_TieredCostUsd() public view {
        assertEq(nft.priceAtIndex(777), 30000);
        assertEq(nft.priceAtIndex(778), 150000);
        assertEq(nft.priceAtIndex(3112), 250000);
        assertEq(nft.priceAtIndex(5445), 350000);
        assertEq(nft.costForUsd(776, 2), 180000); // 30000 + 150000
        assertEq(nft.costForUsd(3110, 2), 400000); // 150000 + 250000
    }

    function test_RevertNonceReplay() public {
        uint256 dl = block.timestamp + 100;
        uint256 cost = nft.costForEth(0, 2);
        bytes memory sig = _pass(user, 2, 7, dl);
        vm.startPrank(user);
        nft.mintWithPass{value: cost}(2, 7, dl, sig);
        vm.expectRevert("nonce used");
        nft.mintWithPass{value: cost}(2, 7, dl, sig);
        vm.stopPrank();
    }

    function test_RevertExpired() public {
        uint256 dl = block.timestamp + 10;
        uint256 cost = nft.costForEth(0, 2);
        bytes memory sig = _pass(user, 2, 1, dl);
        vm.warp(dl + 1);
        vm.prank(user);
        vm.expectRevert("pass expired");
        nft.mintWithPass{value: cost}(2, 1, dl, sig);
    }

    function test_RevertBadQuota() public {
        uint256 dl = block.timestamp + 100;
        uint256 cost = nft.costForEth(0, 11);
        bytes memory sig = _pass(user, 11, 1, dl);
        vm.prank(user);
        vm.expectRevert("bad quota");
        nft.mintWithPass{value: cost}(11, 1, dl, sig);
    }

    function test_RevertWalletCapAcrossPasses() public {
        uint256 dl = block.timestamp + 100;
        vm.startPrank(user);
        nft.mintWithPass{value: nft.costForEth(0, 7)}(7, 1, dl, _pass(user, 7, 1, dl));
        uint256 cost2 = nft.costForEth(7, 5);
        bytes memory sig2 = _pass(user, 5, 2, dl);
        vm.expectRevert("wallet cap");
        nft.mintWithPass{value: cost2}(5, 2, dl, sig2);
        vm.stopPrank();
    }

    function test_RevertBadSigner() public {
        uint256 dl = block.timestamp + 100;
        uint256 cost = nft.costForEth(0, 2);
        bytes32 d = nft.passDigest(user, 2, 1, dl);
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(0xBADBAD, d);
        vm.prank(user);
        vm.expectRevert("bad signer");
        nft.mintWithPass{value: cost}(2, 1, dl, abi.encodePacked(r, s, v));
    }

    function test_RevertWrongWallet() public {
        uint256 dl = block.timestamp + 100;
        uint256 cost = nft.costForEth(0, 2);
        bytes memory sig = _pass(user, 2, 1, dl); // ký cho user
        address other = address(0xCAFE);
        vm.deal(other, 1 ether);
        vm.prank(other);
        vm.expectRevert("bad signer");
        nft.mintWithPass{value: cost}(2, 1, dl, sig);
    }

    function test_RevertSaleOff() public {
        nft.setSaleActive(false);
        uint256 dl = block.timestamp + 100;
        uint256 cost = nft.costForEth(0, 1);
        bytes memory sig = _pass(user, 1, 1, dl);
        vm.prank(user);
        vm.expectRevert("sale off");
        nft.mintWithPass{value: cost}(1, 1, dl, sig);
    }

    function test_Withdraw() public {
        uint256 cost = nft.costForEth(0, 3);
        bytes memory sig = _pass(user, 3, 1, block.timestamp + 100);
        vm.prank(user);
        nft.mintWithPass{value: cost}(3, 1, block.timestamp + 100, sig);
        nft.withdraw(address(0xD00D));
        assertEq(address(0xD00D).balance, cost);
    }

    function test_SoldOut() public {
        uint256 minted; uint256 n = 1; uint256 dl = block.timestamp + 100;
        while (minted + 10 <= MAXS) {
            address w = address(uint160(0x1000 + minted));
            vm.deal(w, 1 ether);
            vm.startPrank(w);
            uint256 cost = nft.costForEth(minted, 10);
            nft.mintWithPass{value: cost}(10, n, dl, _pass(w, 10, n, dl));
            vm.stopPrank();
            minted += 10; n++;
        }
        assertEq(nft.totalSupply(), MAXS);
        uint256 cost = nft.costForEth(MAXS, 1);
        bytes memory sig = _pass(user, 1, 9999, dl);
        vm.prank(user);
        vm.expectRevert("sold out");
        nft.mintWithPass{value: cost}(1, 9999, dl, sig);
    }

    receive() external payable {}
}
