#!/usr/bin/env python3
"""
rarity.py — Tính rarity ranking từ traits của bộ metadata.

Dùng Trait Rarity Score (kiểu rarity.tools): score = Σ 1/(freq_của_trait / tổng).
Trait càng hiếm điểm càng cao → tổng cao = rank tốt.

OpenSea KHÔNG cần rank trong metadata (nó tự tính OpenRarity từ phân bố traits).
Nên ta KHÔNG ghi rank vào file JSON — chỉ xuất bảng local:
  - rarity_ranking.csv  (token_id, rank, score, từng trait)
  - trait_distribution.csv  (trait_type, value, count, percent)

  python3 rarity.py
"""
import csv
import glob
import json
import os
from collections import Counter, defaultdict

OUT = "/Users/loserzx/Desktop/chamau/out"
META = os.path.join(OUT, "metadata")


def main():
    files = sorted(glob.glob(os.path.join(META, "*.json")),
                   key=lambda p: int(os.path.splitext(os.path.basename(p))[0]))
    total = len(files)
    tokens = []
    counts = defaultdict(Counter)  # counts[trait_type][value] = số token

    for p in files:
        with open(p) as f:
            m = json.load(f)
        tid = int(os.path.splitext(os.path.basename(p))[0])
        attrs = {a["trait_type"]: a["value"] for a in m["attributes"]}
        tokens.append((tid, attrs))
        for tt, v in attrs.items():
            counts[tt][v] += 1

    trait_types = list(counts.keys())

    # rarity score mỗi token
    scored = []
    for tid, attrs in tokens:
        score = 0.0
        for tt in trait_types:
            v = attrs.get(tt)
            freq = counts[tt][v] / total
            score += 1.0 / freq
        scored.append((tid, score, attrs))

    scored.sort(key=lambda x: -x[1])

    # ghi ranking
    rank_path = os.path.join(OUT, "rarity_ranking.csv")
    with open(rank_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["rank", "token_id", "rarity_score"] + trait_types)
        for rank, (tid, score, attrs) in enumerate(scored, 1):
            w.writerow([rank, tid, round(score, 2)] + [attrs.get(tt, "") for tt in trait_types])

    # phân bố trait
    dist_path = os.path.join(OUT, "trait_distribution.csv")
    with open(dist_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["trait_type", "value", "count", "percent"])
        for tt in trait_types:
            for v, c in counts[tt].most_common():
                w.writerow([tt, v, c, f"{100*c/total:.2f}%"])

    print(f"Tổng token: {total}")
    print(f"→ {rank_path}")
    print(f"→ {dist_path}\n")
    print("TOP 5 hiếm nhất:")
    for rank, (tid, score, attrs) in enumerate(scored[:5], 1):
        print(f"  #{rank}  token {tid}  score={score:.1f}  "
              + " | ".join(f"{k}={v}" for k, v in attrs.items()))
    print("\nSố giá trị mỗi trait:")
    for tt in trait_types:
        print(f"  {tt}: {len(counts[tt])} value")


if __name__ == "__main__":
    main()
