"""Long-sequence runs (low-memory forward, Kaggle T4): tables + the pre-registered checks H21-H25.

    python analysis/aggregate_long.py
Hypotheses: results/longseq_plan.md. Standard-forward N=200 rows for H22 come from the fresh-set3a/3b kernels.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
SINGLE = {"tfvggt-7scenes-longd": "chess", "tfvggt-7scenes-longe": "chess"}  # one-scene uploads lose the scene folder


def rows(pattern):
    out = []
    for f in sorted(R.glob(pattern)):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                r["scene"] = SINGLE.get(r["scene"], r["scene"])
                out.append(r)
    return out


def main():
    low = rows("long[abcd]/*.jsonl")
    std_oom = rows("longe/*.jsonl")
    std200 = [r for r in rows("fresh-set3[ab]/*.jsonl") if r["frames"] == 200]
    d = defaultdict(dict)
    for r in low:
        d[(r["scene"], r["seq"], r["frames"])][r["config"]] = r

    print("#### Low-memory forward on a T4 (per sequence)\n")
    print("| scene | seq | N (frames used) | config | AUC@30 | Chamfer | time | peak GB |")
    print("|---|---|---|---|---|---|---|---|")
    for k in sorted(d, key=lambda k: (k[2], k[0])):
        for c in ("B1", "AV-s4", "AVE-s4e36"):
            if c in d[k]:
                r = d[k][c]
                print(f"| {k[0]} | {k[1]} | {k[2]} ({r.get('n_used', k[2])}) | {c} | {r['auc30']:.1f} | "
                      f"{r['chamfer']:.3f} | {r['time']:.0f} s | {r['peak_gb']:.2f} |")

    print("\n#### Pre-registered checks\n")
    oom = {r["config"]: r.get("oom", False) for r in std_oom}
    peak = max(r["peak_gb"] for r in low)
    cover = all(any(k[2] == n and c in d[k] for k in d) for c, ns in
                (("B1", [400]), ("AV-s4", [400, 800]), ("AVE-s4e36", [400, 800])) for n in ns)
    print(f"H21: standard forward OOM at N=400 {oom}; low-memory runs done for every planned config/N: {cover}; "
          f"max peak {peak:.2f} GB -> {all(oom.get(c) for c in ('B1', 'AV-s4', 'AVE-s4e36')) and cover and peak <= 10}")

    std = {(r["scene"], r["seq"]): r for r in std200 if r["config"] == "AVE-s4e36"}
    pairs = [(d[k]["AVE-s4e36"]["auc30"], std[k[:2]]["auc30"]) for k in d
             if k[2] == 200 and "AVE-s4e36" in d[k] and k[:2] in std]
    diff = np.array([a - b for a, b in pairs])
    print(f"H22: N=200 low-memory − standard AUC over {len(diff)} sequences: mean {diff.mean():+.2f}, "
          f"max |diff| {np.abs(diff).max():.2f} -> {abs(diff.mean()) <= 0.3}")

    k400 = [k for k in d if k[2] == 400 and all(c in d[k] for c in ("B1", "AV-s4", "AVE-s4e36"))]
    sp400 = np.mean([d[k]["B1"]["time"] for k in k400]) / np.mean([d[k]["AVE-s4e36"]["time"] for k in k400])
    k800 = [k for k in d if k[2] == 800 and "B1" in d[k] and "AVE-s4e36" in d[k]]
    sp800 = [d[k]["B1"]["time"] / d[k]["AVE-s4e36"]["time"] for k in k800]
    print(f"H23: N=400 speed-up AVE vs B1 over {len(k400)} sequences {sp400:.2f}x (≥5); N=800 {[round(x, 2) for x in sp800]} "
          f"(≥8) -> {sp400 >= 5 and bool(sp800) and all(x >= 8 for x in sp800)}")
    b1 = np.array([d[k]["B1"]["auc30"] for k in k400])
    av = np.array([d[k]["AV-s4"]["auc30"] for k in k400])
    ave = np.array([d[k]["AVE-s4e36"]["auc30"] for k in k400])
    print(f"H24: N=400 AVE − B1 mean {np.mean(ave - b1):+.2f} (≥ −1.0), AVE − AV-s4 mean {np.mean(ave - av):+.2f} (≥ 0) "
          f"-> {np.mean(ave - b1) >= -1.0 and np.mean(ave - av) >= 0}")
    k8 = [k for k in d if k[2] == 800 and "AV-s4" in d[k] and "AVE-s4e36" in d[k]]
    x = np.array([d[k]["AVE-s4e36"]["auc30"] - d[k]["AV-s4"]["auc30"] for k in k8])
    print(f"H25: N=800 AVE − AV-s4 over {len(x)} sequences: mean {x.mean():+.2f}, per sequence "
          f"{dict(zip([k[0] for k in k8], np.round(x, 1)))} -> {x.mean() >= 0}")


if __name__ == "__main__":
    main()
