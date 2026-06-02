"use client";

import { useEffect, useRef, useState } from "react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount, useReadContract } from "wagmi";
import { readContract, writeContract, waitForTransactionReceipt } from "@wagmi/core";
import { formatEther } from "viem";
import { config } from "@/lib/wagmi";
import { ABI, CONTRACT_ADDRESS, AGENT_URL } from "@/lib/contract";

function phaseOf(m: number) {
  if (m < 777) return "Phase 1 · $0.03";
  if (m < 3111) return "Phase 2 · $0.15";
  if (m < 5444) return "Phase 3 · $0.25";
  return "Phase 4 · $0.35";
}

type Pass = { quota: number; nonce: string; deadline: number; signature: `0x${string}` };
type Phase = "idle" | "playing" | "solved" | "missed" | "minting" | "done";

export default function Mint() {
  const { address, isConnected } = useAccount();
  const [phase, setPhase] = useState<Phase>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [masked, setMasked] = useState("");
  const [revealed, setRevealed] = useState(0);
  const [guess, setGuess] = useState("");
  const [pass, setPass] = useState<Pass | null>(null);
  const [costEst, setCostEst] = useState<bigint | null>(null);
  const [msg, setMsg] = useState("");
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: total } = useReadContract({ address: CONTRACT_ADDRESS, abi: ABI, functionName: "maxSupply" });
  const { data: minted } = useReadContract({ address: CONTRACT_ADDRESS, abi: ABI, functionName: "totalSupply" });

  // ước tính chi phí chính xác theo phase hiện tại khi vừa khóa được quota
  useEffect(() => {
    if (!pass) { setCostEst(null); return; }
    (async () => {
      try {
        const c = (await readContract(config, {
          address: CONTRACT_ADDRESS, abi: ABI, functionName: "costForEth",
          args: [BigInt(Number(minted ?? 0n)), BigInt(pass.quota)],
        })) as bigint;
        setCostEst(c);
      } catch { setCostEst(null); }
    })();
  }, [pass, minted]);

  const stopPoll = () => { if (poll.current) { clearInterval(poll.current); poll.current = null; } };
  useEffect(() => () => stopPoll(), []);

  async function start() {
    setMsg(""); setPass(null); setGuess("");
    const r = await fetch(`${AGENT_URL}/api/session`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ wallet: address }),
    });
    const d = await r.json();
    if (!r.ok) return setMsg(d.error ?? "lỗi tạo session");
    setSessionId(d.sessionId); setMasked(d.masked); setRevealed(0); setPhase("playing");
    stopPoll();
    poll.current = setInterval(async () => {
      const p = await fetch(`${AGENT_URL}/api/peek/${d.sessionId}`).then((x) => x.json()).catch(() => null);
      if (p && !p.error) { setMasked(p.masked); setRevealed(p.revealed); }
    }, 1000);
  }

  async function submitGuess(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId || !guess.trim()) return;
    const r = await fetch(`${AGENT_URL}/api/guess`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ sessionId, guess }),
    });
    const d = await r.json();
    if (!r.ok) { setMsg(d.error ?? "lỗi"); return; }
    if (!d.correct) { setMasked(d.masked); setRevealed(d.revealed); setGuess(""); setMsg("Sai, thử lại!"); return; }
    stopPoll();
    if (d.quota === 0 || !d.pass) { setPhase("missed"); setMsg(d.reason ?? "trượt suất"); return; }
    setPass(d.pass); setPhase("solved"); setMsg("");
  }

  async function mintNow() {
    if (!pass || !address) return;
    try {
      setPhase("minting"); setMsg("Mint...");
      // đọc cost ETH hiện tại + đệm 5% chống trượt oracle/totalMinted; contract hoàn phần dư
      const base = (await readContract(config, {
        address: CONTRACT_ADDRESS, abi: ABI, functionName: "costForEth",
        args: [BigInt(Number(minted ?? 0n)), BigInt(pass.quota)],
      })) as bigint;
      const value = base + base / 20n;
      const h = await writeContract(config, {
        address: CONTRACT_ADDRESS, abi: ABI, functionName: "mintWithPass",
        args: [BigInt(pass.quota), BigInt(pass.nonce), BigInt(pass.deadline), pass.signature],
        value,
      });
      await waitForTransactionReceipt(config, { hash: h });
      setPhase("done"); setMsg("");
    } catch (err: any) {
      setPhase("solved"); setMsg("❌ " + (err?.shortMessage ?? err?.message ?? "mint lỗi").split("\n")[0]);
    }
  }

  const cost = costEst != null ? Number(formatEther(costEst)).toFixed(5) : "…";
  const phaseLabel = minted != null ? phaseOf(Number(minted)) : "";
  const remain = pass ? Math.max(0, pass.deadline - Math.floor(Date.now() / 1000)) : 0;

  return (
    <main className="wrap">
      <div>
        <div className="title">Mythos Dots</div>
        <div className="sub">Giải đoán chữ → khóa suất → mint. Nhanh = quota to.</div>
      </div>
      <ConnectButton />
      {total != null && minted != null && (
        <div className="sub">Đã mint {Number(minted)} / {Number(total)}{phaseLabel ? ` · ${phaseLabel}` : ""}</div>
      )}

      <div className="card">
        {phase === "idle" && (
          <button className="mint" disabled={!isConnected} onClick={start}>
            {isConnected ? "Bắt đầu đoán chữ" : "Kết nối ví trước"}
          </button>
        )}

        {phase === "playing" && (
          <>
            <div className="row"><span>Đã lộ</span><span>{revealed}/{masked.length} chữ</span></div>
            <div style={{ fontSize: 34, letterSpacing: 8, fontWeight: 800, textAlign: "center" }}>
              {masked.split("").join(" ")}
            </div>
            <div className="sub">Mỗi 2s lộ thêm 1 chữ. Đoán càng sớm quota càng to (tối đa 10).</div>
            <form onSubmit={submitGuess} className="qty">
              <input value={guess} onChange={(e) => setGuess(e.target.value)} placeholder="từ của bạn"
                style={{ flex: 1, padding: 12, borderRadius: 10, border: "1px solid #333", background: "#111", color: "#fff", fontSize: 18 }} autoFocus />
              <button className="mint" style={{ width: "auto", padding: "12px 20px" }} type="submit">Đoán</button>
            </form>
          </>
        )}

        {(phase === "solved" || phase === "minting") && pass && (
          <>
            <div className="row"><span>🎉 Quota khóa được</span><span>{pass.quota} NFT</span></div>
            <div className="row"><span>Giá (~)</span><span>{cost} ETH</span></div>
            <div className="row"><span>Hết hạn mint sau</span><span>{remain}s</span></div>
            <button className="mint" disabled={phase === "minting" || remain <= 0} onClick={mintNow}>
              {phase === "minting" ? "Đang xử lý..." : remain <= 0 ? "Pass hết hạn" : `Mint ${pass.quota} — ~${cost} ETH`}
            </button>
          </>
        )}

        {phase === "missed" && (
          <>
            <div className="sub">😢 {msg || "Trượt suất."}</div>
            <button className="mint" onClick={() => setPhase("idle")}>Thử lại</button>
          </>
        )}

        {phase === "done" && (
          <>
            <div className="sub">✅ Mint thành công {pass?.quota} NFT!</div>
            <button className="mint" onClick={() => { setPass(null); setPhase("idle"); }}>Chơi tiếp</button>
          </>
        )}

        {msg && phase !== "missed" && <div className="status">{msg}</div>}
      </div>
    </main>
  );
}
