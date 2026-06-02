// Ký EIP-712 Pass bằng viem (giống agent) — để test khớp với contract Solidity.
// Dùng: node sign_pass.mjs <contract> <chainId> <wallet> <quota> <nonce> <deadline> <agentPk>
import { privateKeyToAccount } from "viem/accounts";

const [, , contract, chainId, wallet, quota, nonce, deadline, pk] = process.argv;
const account = privateKeyToAccount(pk);
const sig = await account.signTypedData({
  domain: { name: "MythosDots", version: "1", chainId: Number(chainId), verifyingContract: contract },
  types: {
    Pass: [
      { name: "wallet", type: "address" },
      { name: "quota", type: "uint256" },
      { name: "nonce", type: "uint256" },
      { name: "deadline", type: "uint256" },
    ],
  },
  primaryType: "Pass",
  message: { wallet, quota: BigInt(quota), nonce: BigInt(nonce), deadline: BigInt(deadline) },
});
console.log(sig);
