"""Fresh-set validation (11 unseen 7-Scenes sequences, Kaggle T4): tables + the pre-registered checks H16-H20.

    python analysis/aggregate_fresh.py
Hypotheses are in results/fresh_plan.md; the checks below apply them literally.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
CONFIGS = ["B1", "AV-s4", "AVE-s4e36", "AVEK-s4e36k10", "AVEK-s4e36k20", "K-r2k10"]
MAIN = "AVEK-s4e36k10"


def load():
    d = defaultdict(dict)
    for f in sorted(R.glob("fresh-*/*.jsonl")):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                d[(r["scene"], r["seq"], r["frames"])][r["config"]] = r
    return d


def col(d, ks, c, key="auc30"):
    return np.array([d[k][c][key] for k in ks])


def main():
    d = load()
    stats = {}
    for n in (50, 100, 200):
        ks = sorted(k for k in d if k[2] == n and all(c in d[k] for c in CONFIGS))
        b1, tb = col(d, ks, "B1"), col(d, ks, "B1", "time")
        print(f"\n#### N = {n} ({len(ks)} sequences)\n")
        print("| config | AUC@30 | Δ vs B1 | worst Δ | within 2 | Chamfer | fid_pose | T4 time | speed-up |")
        print("|---|---|---|---|---|---|---|---|---|")
        for c in CONFIGS:
            a, t = col(d, ks, c), col(d, ks, c, "time")
            dl = a - b1
            fid = np.mean([d[k][c].get("fid_pose", np.nan) for k in ks])
            print(f"| {c} | {a.mean():.1f} | {dl.mean():+.2f} | {dl.min():+.1f} | {(dl >= -2).sum()}/{len(ks)} | "
                  f"{col(d, ks, c, 'chamfer').mean():.3f} | {fid:.1f} | {t.mean():.0f} s | {tb.mean() / t.mean():.1f}× |")
            stats[(n, c)] = dict(auc=a.mean(), delta=dl.mean(), worst=dl.min(), within=(dl >= -2).sum(),
                                 n=len(ks), time=t.mean(), x=a)
        for a_, b_ in [(MAIN, "AV-s4"), ("AVE-s4e36", "AV-s4"), (MAIN, "K-r2k10"), ("AVEK-s4e36k20", "AV-s4")]:
            x = stats[(n, a_)]["x"] - stats[(n, b_)]["x"]
            p = wilcoxon(x).pvalue if np.any(x != 0) else 1.0
            print(f"\n{a_} − {b_}: mean {x.mean():+.2f}, wins {(x > 0).sum()}/{len(x)}, Wilcoxon p = {p:.3f}")

    print("\n#### Pre-registered checks\n")
    s = stats
    h16 = [(s[(n, MAIN)]["auc"] >= s[(n, "AV-s4")]["auc"], s[(n, MAIN)]["worst"] > s[(n, "AV-s4")]["worst"])
           for n in (50, 100, 200)]
    print("H16 (mean ≥ AV-s4 and smaller worst drop, every N):", all(a and b for a, b in h16), h16)
    h17 = [int(s[(n, MAIN)]["within"]) == s[(n, MAIN)]["n"] for n in (100, 200)]
    print("H17 (all sequences within 2 of B1 at N=100, 200):", all(h17), h17)
    h18 = [round(float(s[(n, MAIN)]["delta"]), 2) for n in (100, 200)]
    print("H18 (mean Δ ≥ −0.5 at N=100, 200):", all(x >= -0.5 for x in h18), h18)
    h19 = [s[(n, "AVE-s4e36")]["auc"] >= s[(n, "AV-s4")]["auc"] for n in (50, 100, 200)]
    print("H19 (AVE-s4e36 mean ≥ AV-s4, every N):", all(h19), h19)
    speed = s[(200, "K-r2k10")]["time"] / s[(200, MAIN)]["time"]
    acc = s[(200, MAIN)]["auc"] - s[(200, "K-r2k10")]["auc"]
    print(f"H20 (≥10% faster than K-r2k10 and AUC ≥ K-r2k10 − 0.2 at N=200): {speed >= 1.1 and acc >= -0.2} "
          f"(K-r2k10 time / ours = {speed:.2f}, AUC diff = {acc:+.2f})")


if __name__ == "__main__":
    main()
