import { getDefaultConfig } from "@rainbow-me/rainbowkit";
import { mainnet, sepolia } from "wagmi/chains";

export const TARGET_CHAIN =
  process.env.NEXT_PUBLIC_CHAIN === "mainnet" ? mainnet : sepolia;

export const config = getDefaultConfig({
  appName: "Mythos Dots",
  projectId: process.env.NEXT_PUBLIC_WC_PROJECT_ID ?? "",
  chains: [sepolia, mainnet],
  ssr: true,
});
