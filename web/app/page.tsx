"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { ConnectButton } from "@rainbow-me/rainbowkit";
import { useAccount, useReadContract } from "wagmi";
import { readContract, writeContract, waitForTransactionReceipt } from "@wagmi/core";
import { formatEther } from "viem";
import { config } from "@/lib/wagmi";
import { ABI, CONTRACT_ADDRESS, AGENT_URL } from "@/lib/contract";

type Pass = { quota: number; nonce: string; deadline: number; signature: `0x${string}` };
type Phase = "idle" | "playing" | "solved" | "missed" | "minting" | "done";

const GRADS = [
  ["#fa709a", "#fee140"], ["#6a11cb", "#2575fc"], ["#5ee7df", "#b490ca"],
  ["#f093fb", "#f5576c"], ["#a18cd1", "#fbc2eb"], ["#84fab0", "#8fd3f4"],
  ["#fccb90", "#d57eeb"], ["#13547a", "#80d0c7"],
];

function DotField() {
  const dots = useMemo(
    () =>
      Array.from({ length: 34 }, (_, i) => {
        const g = GRADS[i % GRADS.length];
        return {
          left: (i * 37) % 100,
          top: (i * 61) % 100,
          size: 34 + ((i * 53) % 90),
          bg: `linear-gradient(135deg, ${g[0]}, ${g[1]})`,
          dur: 11 + (i % 9),
          delay: -(i % 11),
          dx: ((i % 7) - 3) * 14,
          dy: ((i % 5) - 2) * 16,
        };
      }),
    []
  );
  return (
    <div className="dotfield">
      {dots.map((d, i) => (
        <span
          key={i}
          className="dot"
          style={
            {
              left: `${d.left}%`,
              top: `${d.top}%`,
              width: d.size,
              height: d.size,
              background: d.bg,
              "--dur": `${d.dur}s`,
              "--delay": `${d.delay}s`,
              "--dx": `${d.dx}px`,
              "--dy": `${d.dy}px`,
            } as React.CSSProperties
          }
        />
      ))}
    </div>
  );
}

function phaseOf(m: number) {
  if (m < 777) return "Phase 1 · $0.03";
  if (m < 3111) return "Phase 2 · $0.15";
  if (m < 5444) return "Phase 3 · $0.25";
  return "Phase 4 · $0.35";
}

export default function Mint() {
  const { address, isConnected } = useAccount();
  const [phase, setPhase] = useState<Phase>("idle");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [masked, setMasked] = useState("");
  const [revealed, setRevealed] = useState(0);
  const [guess, setGuess] = useState("");
  const [pass, setPass] = useState<Pass | null>(null);
  const [costEst, setCostEst] = useState<bigint | null>(null);
  const [starting, setStarting] = useState(false);
  const [note, setNote] = useState("");
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  const { data: total } = useReadContract({ address: CONTRACT_ADDRESS, abi: ABI, functionName: "maxSupply" });
  const { data: minted } = useReadContract({ address: CONTRACT_ADDRESS, abi: ABI, functionName: "totalSupply" });

  // warm up the agent (Render free sleeps) so the first "Play" is fast
  useEffect(() => {
    fetch(`${AGENT_URL}/api/state`).catch(() => {});
  }, []);

  const stopPoll = () => { if (poll.current) { clearInterval(poll.current); poll.current = null; } };
  useEffect(() => () => stopPoll(), []);

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

  async function start() {
    setNote(""); setPass(null); setGuess(""); setStarting(true);
    const slow = setTimeout(() => setNote("Waking the mint server… first load can take ~40s."), 3500);
    try {
      const r = await fetch(`${AGENT_URL}/api/session`, {
        method: "POST", headers: { "content-type": "application/json" },
        body: JSON.stringify({ wallet: address }),
      });
      const d = await r.json();
      if (!r.ok) { setNote(d.error ?? "Failed to start."); return; }
      setSessionId(d.sessionId); setMasked(d.masked); setRevealed(0); setNote(""); setPhase("playing");
      stopPoll();
      poll.current = setInterval(async () => {
        const p = await fetch(`${AGENT_URL}/api/peek/${d.sessionId}`).then((x) => x.json()).catch(() => null);
        if (p && !p.error) { setMasked(p.masked); setRevealed(p.revealed); }
      }, 1000);
    } catch {
      setNote("Cannot reach the mint server. Try again.");
    } finally {
      clearTimeout(slow); setStarting(false);
    }
  }

  async function submitGuess(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId || !guess.trim()) return;
    const r = await fetch(`${AGENT_URL}/api/guess`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ sessionId, guess }),
    });
    const d = await r.json();
    if (!r.ok) { setNote(d.error ?? "Error"); return; }
    if (!d.correct) { setMasked(d.masked); setRevealed(d.revealed); setGuess(""); setNote("Not it — keep guessing!"); return; }
    stopPoll();
    if (d.quota === 0 || !d.pass) { setPhase("missed"); setNote(d.reason ?? "Missed the allocation."); return; }
    setPass(d.pass); setPhase("solved"); setNote("");
  }

  async function mintNow() {
    if (!pass || !address) return;
    try {
      setPhase("minting"); setNote("Confirm in your wallet…");
      const base = (await readContract(config, {
        address: CONTRACT_ADDRESS, abi: ABI, functionName: "costForEth",
        args: [BigInt(Number(minted ?? 0n)), BigInt(pass.quota)],
      })) as bigint;
      const value = base + base / 20n; // +5% buffer for oracle drift; contract refunds the rest
      const h = await writeContract(config, {
        address: CONTRACT_ADDRESS, abi: ABI, functionName: "mintWithPass",
        args: [BigInt(pass.quota), BigInt(pass.nonce), BigInt(pass.deadline), pass.signature],
        value,
      });
      setNote("Minting…");
      await waitForTransactionReceipt(config, { hash: h });
      setPhase("done"); setNote("");
    } catch (err: any) {
      setPhase("solved");
      setNote("✗ " + (err?.shortMessage ?? err?.message ?? "Mint failed").split("\n")[0]);
    }
  }

  const cost = costEst != null ? Number(formatEther(costEst)).toFixed(5) : "…";
  const supply = total ? Number(total) : 7777;
  const done = minted ? Number(minted) : 0;
  const remain = pass ? Math.max(0, pass.deadline - Math.floor(Date.now() / 1000)) : 0;

  return (
    <main className="app">
      <DotField />
      <header className="topbar">
        <div className="brand">◐ <span>Mythos Dots</span></div>
        <ConnectButton showBalance={false} chainStatus="icon" />
      </header>

      <section className="stage">
        <h1 className="hero-title">Mythos Dots</h1>
        <p className="hero-sub">7777 generative pixel-dot NFTs. Solve the word, lock your allocation, mint. Faster = bigger quota.</p>
        <div className="pill"><b>{done}</b>/{supply} minted · {phaseOf(done)}</div>

        {phase === "idle" && (
          <>
            <button className="orb" onClick={start} disabled={!isConnected || starting}>
              {starting ? "Waking…" : isConnected ? "Tap to Play" : "Connect wallet"}
            </button>
            <div className="note">{note || (isConnected ? "Guess the hidden word to lock a mint allocation." : "Connect your wallet (Sepolia) to begin.")}</div>
          </>
        )}

        {phase === "playing" && (
          <div className="panel">
            <div className="row"><span>Revealed</span><b>{revealed}/{masked.length} letters</b></div>
            <div className="word">{masked.split("").join(" ")}</div>
            <div className="note">A new letter is revealed every 2s. Guess sooner for a bigger quota (up to 10).</div>
            <form onSubmit={submitGuess} className="guess-form">
              <input className="input" value={guess} onChange={(e) => setGuess(e.target.value)} placeholder="your guess" autoFocus />
              <button className="btn" type="submit">Guess</button>
            </form>
            {note && <div className="note">{note}</div>}
          </div>
        )}

        {(phase === "solved" || phase === "minting") && pass && (
          <div className="panel">
            <div className="row"><span>🎉 Allocation locked</span><b>{pass.quota} NFT</b></div>
            <div className="row"><span>Price</span><b>~{cost} ETH</b></div>
            <div className="row"><span>Expires in</span><b>{remain}s</b></div>
            <button className="btn full" disabled={phase === "minting" || remain <= 0} onClick={mintNow}>
              {phase === "minting" ? <><span className="spinner" />Working…</> : remain <= 0 ? "Pass expired" : `Mint ${pass.quota} · ~${cost} ETH`}
            </button>
            <div className="note err">{note}</div>
          </div>
        )}

        {phase === "missed" && (
          <div className="panel">
            <div className="note">😶‍🌫️ {note || "Allocation pool is full — missed it."}</div>
            <button className="btn ghost full" onClick={() => { setPhase("idle"); setNote(""); }}>Try again</button>
          </div>
        )}

        {phase === "done" && (
          <div className="panel">
            <div className="note ok">✓ Minted {pass?.quota} NFT successfully!</div>
            <button className="btn full" onClick={() => { setPass(null); setPhase("idle"); setNote(""); }}>Play again</button>
          </div>
        )}
      </section>
    </main>
  );
}
