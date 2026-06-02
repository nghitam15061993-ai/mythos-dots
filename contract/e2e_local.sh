#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.foundry/bin:$PATH"
cd "$(dirname "$0")"

RPC=http://127.0.0.1:8545
DEPLOYER_PK=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
USER_PK=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
USER=0x70997970C51812dc3A010C7d01b50e0d17dc79C8
AGENT_PK=0x2a871d0798f97d79848a013d4936a73bf4cc922c825d33c1cf7073dff6d409c6
AGENT=0xa0Ee7A142d267C1f36714E4a8F75612F20a79720
ROYALTY=0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
BASEURI="ipfs://bafybeicdxyjzpiuiyd4snbqp3v2defc7dep2w2ajjtqkycwl3h6reejb5a/"

addr() { python3 -c "import sys,json;print(json.load(sys.stdin)['deployedTo'])"; }

echo "== deploy MockFeed (\$2000/ETH) =="
FEED=$(forge create test/MythosDots.t.sol:MockFeed --rpc-url $RPC --private-key $DEPLOYER_PK --broadcast --json --constructor-args 200000000000 | addr)
echo "FEED=$FEED"

echo "== deploy MythosDots =="
NFT=$(forge create src/MythosDots.sol:MythosDots --rpc-url $RPC --private-key $DEPLOYER_PK --broadcast --json \
  --constructor-args 7777 $FEED $AGENT "$BASEURI" $ROYALTY | addr)
echo "NFT=$NFT"

echo "== setSaleActive(true) =="
cast send $NFT "setSaleActive(bool)" true --rpc-url $RPC --private-key $DEPLOYER_PK >/dev/null

QUOTA=3; NONCE=1; DEADLINE=9999999999
echo "== agent (viem) ký pass quota=$QUOTA =="
SIG=$(node ../agent/sign_pass.mjs $NFT 31337 $USER $QUOTA $NONCE $DEADLINE $AGENT_PK)
echo "SIG=$SIG"

COST=$(cast call $NFT "costForEth(uint256,uint256)(uint256)" 0 $QUOTA --rpc-url $RPC | awk '{print $1}')
echo "COST(wei)=$COST  (~$(cast from-wei $COST) ETH)"

echo "== user mint (trả ETH) =="
cast send $NFT "mintWithPass(uint256,uint256,uint256,bytes)" $QUOTA $NONCE $DEADLINE $SIG \
  --value $COST --rpc-url $RPC --private-key $USER_PK >/dev/null

echo "== verify =="
echo "balanceOf(user) = $(cast call $NFT 'balanceOf(address)(uint256)' $USER --rpc-url $RPC)"
echo "ownerOf(1)      = $(cast call $NFT 'ownerOf(uint256)(address)' 1 --rpc-url $RPC)"
echo "totalSupply     = $(cast call $NFT 'totalSupply()(uint256)' --rpc-url $RPC)"
echo "tokenURI(1)     = $(cast call $NFT 'tokenURI(uint256)(string)' 1 --rpc-url $RPC)"
echo "contract bal    = $(cast balance $NFT --rpc-url $RPC) wei"
echo ""
echo "== test replay (phải revert nonce used) =="
if cast send $NFT "mintWithPass(uint256,uint256,uint256,bytes)" $QUOTA $NONCE $DEADLINE $SIG \
   --value $COST --rpc-url $RPC --private-key $USER_PK >/dev/null 2>&1; then
  echo "❌ KHÔNG revert — LỖI"
else
  echo "✅ replay bị revert đúng"
fi
