import express from "express";
import cors from "cors";
import { readFileSync } from "node:fs";
import { randomBytes } from "node:crypto";
import {
  createPublicClient,
  http,
  getAddress,
  type Address,
} from "viem";
import { privateKeyToAccount } from "viem/accounts";

// ───────────────────────── config ─────────────────────────
const {
  AGENT_PRIVATE_KEY,
  CONTRACT_ADDRESS,
  CHAIN_ID,
  RPC_URL,
  PORT = "8787",
  MINT_WINDOW_SEC = "120",
  SHOW_DEFINITION = "false",
} = process.env;

if (!AGENT_PRIVATE_KEY || !CONTRACT_ADDRESS || !CHAIN_ID || !RPC_URL) {
  throw new Error("Thiếu env: AGENT_PRIVATE_KEY / CONTRACT_ADDRESS / CHAIN_ID / RPC_URL");
}

const account = privateKeyToAccount(AGENT_PRIVATE_KEY as `0x${string}`);
const contract = getAddress(CONTRACT_ADDRESS) as Address;
const chainId = Number(CHAIN_ID);
const windowSec = Number(MINT_WINDOW_SEC);

const client = createPublicClient({ transport: http(RPC_URL) });

const ABI = [
  { type: "function", name: "maxSupply", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { type: "function", name: "totalSupply", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { type: "function", name: "currentPriceEth", stateMutability: "view", inputs: [], outputs: [{ type: "uint256" }] },
  { type: "function", name: "mintedOf", stateMutability: "view", inputs: [{ type: "address" }], outputs: [{ type: "uint256" }] },
] as const;

const EIP712_DOMAIN = {
  name: "MythosDots",
  version: "1",
  chainId,
  verifyingContract: contract,
} as const;
const EIP712_TYPES = {
  Pass: [
    { name: "wallet", type: "address" },
    { name: "quota", type: "uint256" },
    { name: "nonce", type: "uint256" },
    { name: "deadline", type: "uint256" },
  ],
} as const;

const MAX_PER_WALLET = 10;

// ───────────────────────── wordlist ─────────────────────────
let WORDS: string[];
try {
  WORDS = readFileSync(new URL("../words.txt", import.meta.url), "utf8")
    .split("\n").map((w) => w.trim().toUpperCase()).filter(Boolean);
} catch {
  throw new Error("Thiếu words.txt — chạy `npm run fetch-words` trước.");
}
if (WORDS.length < 100) throw new Error("words.txt quá ít từ");
console.log(`Loaded ${WORDS.length} words`);

// ───────────────────────── state ─────────────────────────
type Session = {
  wallet: string;
  word: string;
  start: number;      // ms
  order: number[];    // thứ tự lật chữ
  solved: boolean;
};
const sessions = new Map<string, Session>();
const pending = new Map<string, { quota: number; deadline: number }>(); // nonce(hex) -> ...
const rate = new Map<string, { n: number; ts: number }>();

let maxSupply = 0n;
let priceWei = 0n;

const nowS = () => Date.now() / 1000;
const randInt = (a: number, b: number) => a + Math.floor(Math.random() * (b - a + 1));
const shuffle = (n: number) => {
  const a = [...Array(n).keys()];
  for (let i = n - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
};

const REVEAL_MS = 3500; // lật 1 chữ mỗi 3.5s
function revealedCount(s: Session) {
  return Math.min(s.word.length - 1, Math.floor((Date.now() - s.start) / REVEAL_MS));
}
function masked(s: Session) {
  const show = new Set(s.order.slice(0, revealedCount(s)));
  return s.word.split("").map((c, i) => (show.has(i) ? c : "_")).join("");
}
function quotaForReveal(r: number) {
  if (r <= 1) return randInt(8, 10);
  if (r <= 3) return randInt(5, 7);
  if (r <= 5) return randInt(3, 4);
  return randInt(1, 2);
}
function reservedPending(): number {
  const t = nowS();
  let sum = 0;
  for (const [k, p] of pending) {
    if (p.deadline > t) sum += p.quota; else pending.delete(k);
  }
  return sum;
}
// cache totalSupply + price để không gọi RPC mỗi request (chống rate-limit khi đông)
let _mintedCache = 0n, _mintedAt = 0;
async function getTotalMinted(): Promise<number> {
  if (Date.now() - _mintedAt > 4000) {
    try { _mintedCache = (await client.readContract({ address: contract, abi: ABI, functionName: "totalSupply" })) as bigint; _mintedAt = Date.now(); } catch {}
  }
  return Number(_mintedCache);
}
let _priceCache = 0n, _priceAt = 0;
async function getPriceWei(): Promise<bigint> {
  if (Date.now() - _priceAt > 10000) {
    try { _priceCache = (await client.readContract({ address: contract, abi: ABI, functionName: "currentPriceEth" })) as bigint; _priceAt = Date.now(); } catch {}
  }
  return _priceCache;
}

async function available(): Promise<number> {
  return Number(maxSupply) - (await getTotalMinted()) - reservedPending();
}
function rateOk(wallet: string) {
  const t = Date.now();
  const r = rate.get(wallet);
  if (!r || t - r.ts > 10_000) { rate.set(wallet, { n: 1, ts: t }); return true; }
  if (r.n >= 20) return false;            // ≤20 guess / 10s / ví
  r.n++; return true;
}

// ───────────────────────── server ─────────────────────────
const app = express();
app.use(cors());
app.use(express.json());

app.get("/api/state", async (_req, res) => {
  try {
    const minted = await getTotalMinted();
    const price = await getPriceWei();
    res.json({
      maxSupply: Number(maxSupply),
      totalMinted: minted,
      available: Number(maxSupply) - minted - reservedPending(),
      currentPriceEthWei: price.toString(),
    });
  } catch (e: any) { res.status(500).json({ error: String(e?.message ?? e) }); }
});

app.post("/api/session", async (req, res) => {
  let wallet: string;
  try { wallet = getAddress(req.body?.wallet); } catch { return res.status(400).json({ error: "Invalid wallet" }); }
  // chặn sớm: ví đã đạt trần 10 thì khỏi cho chơi
  try {
    const m = Number(await client.readContract({ address: contract, abi: ABI, functionName: "mintedOf", args: [wallet as Address] }));
    if (m >= MAX_PER_WALLET) return res.status(403).json({ error: "This wallet already minted the max (10 NFTs)." });
  } catch {}
  const word = WORDS[Math.floor(Math.random() * WORDS.length)];
  const sessionId = randomBytes(16).toString("hex");
  const s: Session = { wallet, word, start: Date.now(), order: shuffle(word.length), solved: false };
  sessions.set(sessionId, s);
  res.json({
    sessionId,
    length: word.length,
    masked: masked(s),
    revealEverySec: 3.5,
    ...(SHOW_DEFINITION === "true" ? { hint: "definition-on" } : {}),
  });
});

app.get("/api/peek/:sessionId", (req, res) => {
  const s = sessions.get(req.params.sessionId);
  if (!s) return res.status(404).json({ error: "session không tồn tại" });
  res.json({ masked: masked(s), revealed: revealedCount(s), length: s.word.length, solved: s.solved });
});

app.post("/api/guess", async (req, res) => {
  const { sessionId, guess } = req.body ?? {};
  const s = sessions.get(sessionId);
  if (!s) return res.status(404).json({ error: "session không tồn tại" });
  if (s.solved) return res.status(409).json({ error: "session đã giải xong" });
  if (!rateOk(s.wallet)) return res.status(429).json({ error: "quá nhiều lần đoán, chờ chút" });

  if (String(guess ?? "").trim().toUpperCase() !== s.word) {
    return res.json({ correct: false, masked: masked(s), revealed: revealedCount(s) });
  }

  // ĐÚNG → tính quota theo tốc độ, clamp ví + pool
  const r = revealedCount(s);
  const tier = quotaForReveal(r);
  let mintedOf = 0;
  try {
    mintedOf = Number(await client.readContract({ address: contract, abi: ABI, functionName: "mintedOf", args: [s.wallet as Address] }));
  } catch (e: any) { return res.status(500).json({ error: "rpc fail: " + String(e?.message ?? e) }); }

  const walletRemaining = MAX_PER_WALLET - mintedOf;
  const avail = await available();
  const quota = Math.max(0, Math.min(tier, walletRemaining, avail));

  s.solved = true;
  if (quota <= 0) {
    const reason = avail <= 0 ? "Sold out — pool is full" : "This wallet already minted the max (10 NFTs).";
    return res.json({ correct: true, quota: 0, reason });
  }

  const nonceHex = "0x" + randomBytes(32).toString("hex");
  const nonce = BigInt(nonceHex);
  const deadline = Math.floor(nowS()) + windowSec;

  const signature = await account.signTypedData({
    domain: EIP712_DOMAIN,
    types: EIP712_TYPES,
    primaryType: "Pass",
    message: { wallet: s.wallet as Address, quota: BigInt(quota), nonce, deadline: BigInt(deadline) },
  });

  pending.set(nonceHex, { quota, deadline });
  res.json({
    correct: true,
    pass: { wallet: s.wallet, quota, nonce: nonce.toString(), deadline, signature },
    revealedWhenSolved: r,
  });
});

const port = Number(PORT);
(async () => {
  maxSupply = (await client.readContract({ address: contract, abi: ABI, functionName: "maxSupply" })) as bigint;
  priceWei = (await client.readContract({ address: contract, abi: ABI, functionName: "currentPriceEth" })) as bigint;
  console.log(`agent signer = ${account.address}`);
  console.log(`contract ${contract} chain ${chainId} | maxSupply ${maxSupply} price ${priceWei}`);
  app.listen(port, () => console.log(`agent on :${port}`));
})();
