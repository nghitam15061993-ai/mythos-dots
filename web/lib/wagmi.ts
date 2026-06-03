import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { fallback, http } from "viem";
import { mainnet, sepolia } from "wagmi/chains";

export const TARGET_CHAIN =
  process.env.NEXT_PUBLIC_CHAIN === "mainnet" ? mainnet : sepolia;

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
  chains: [mainnet, sepolia],
  transports: {
    [mainnet.id]: mainnetTransport,
    [sepolia.id]: http("https://ethereum-sepolia-rpc.publicnode.com"),
  },
  ssr: true,
});
