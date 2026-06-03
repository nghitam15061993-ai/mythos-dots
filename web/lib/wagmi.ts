import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { http } from "wagmi";
import { mainnet, sepolia } from "wagmi/chains";

export const TARGET_CHAIN =
  process.env.NEXT_PUBLIC_CHAIN === "mainnet" ? mainnet : sepolia;

export const config = getDefaultConfig({
  appName: "Mythos Dots",
  projectId: process.env.NEXT_PUBLIC_WC_PROJECT_ID ?? "",
  chains: [mainnet, sepolia],
  transports: {
    // RPC tin cậy cho reads (mặc định public; set NEXT_PUBLIC_RPC_URL để dùng Alchemy)
    [mainnet.id]: http(process.env.NEXT_PUBLIC_RPC_URL || "https://eth.llamarpc.com"),
    [sepolia.id]: http("https://ethereum-sepolia-rpc.publicnode.com"),
  },
  ssr: true,
});
