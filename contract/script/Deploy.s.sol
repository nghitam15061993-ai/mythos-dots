// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "forge-std/Script.sol";
import "../src/MythosDots.sol";

contract Deploy is Script {
    function run() external {
        uint256 pk = vm.envUint("PRIVATE_KEY");
        uint256 maxSupply = vm.envUint("MAX_SUPPLY");      // 7777
        address priceFeed = vm.envAddress("PRICE_FEED");   // Chainlink ETH/USD
        address agentSigner = vm.envAddress("AGENT_SIGNER");
        string memory baseURI = vm.envString("BASE_URI");
        address royalty = vm.envAddress("ROYALTY_RECEIVER");

        vm.startBroadcast(pk);
        MythosDots nft = new MythosDots(
            maxSupply, priceFeed, agentSigner, baseURI, royalty
        );
        vm.stopBroadcast();

        console2.log("MythosDots:", address(nft));
    }
}
