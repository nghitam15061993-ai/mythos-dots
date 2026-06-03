import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { fallback, http } from "viem";
import { mainnet } from "wagmi/chains";

export const TARGET_CHAIN = mainnet;

// RPC tin cậy cho reads. Set NEXT_PUBLIC_RPC_URL (Alchemy) để tốt nhất; nếu không, fallback nhiều RPC public.
const mainnetTransport = process.env.NEXT_PUBLIC_RPC_URL
  ? http(process.env.NEXT_PUBLIC_RPC_URL)
  : fallback([
      http("https://ethereum-rpc.publicnode.com"),
      http("https://eth.drpc.org"),
      http("https://1rpc.io/eth"),
    ]);

export const config = getDefaultConfig({
  appName: "Mythos Dots",
  projectId: process.env.NEXT_PUBLIC_WC_PROJECT_ID ?? "",
  chains: [mainnet],
  transports: { [mainnet.id]: mainnetTransport },
  ssr: true,
});
