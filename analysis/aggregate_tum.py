"""TUM RGB-D runs (Kaggle T4): tables + the pre-registered checks H26-H29 (results/tum_plan.md).

    python analysis/aggregate_tum.py
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
CONFIGS = ["B1", "K-r2k10", "AV-s4", "AVE-s4e36", "AVEK-s4e36k10"]
SEEN = "fr1_360"


def main():
    d = defaultdict(dict)
    for f in sorted(R.glob("tum[abc]/*.jsonl")):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                d[(r["scene"], r["frames"])][r["config"]] = r
    for n in (50, 100, 200, 400):
        ks = sorted(k for k in d if k[1] == n)
        print(f"\n#### N = {n}\n")
        print("| sequence | " + " | ".join(CONFIGS) + " |")
        print("|---|" + "---|" * len(CONFIGS))
        for k in ks:
            print(f"| {k[0]} | " + " | ".join(f"{d[k][c]['auc30']:.1f}" if c in d[k] else "–" for c in CONFIGS) + " |")
        rows = []
        for c in CONFIGS:
            ks_c = [k for k in ks if c in d[k]]
            if ks_c:
                a = np.mean([d[k][c]["auc30"] for k in ks_c])
                t = np.mean([d[k][c]["time"] for k in ks_c])
                rows.append(f"{c} {a:.1f} ({t:.0f} s)")
        print("\nmean AUC (time): " + "; ".join(rows))

    print("\n#### Pre-registered checks\n")
    h26 = []
    for n in (50, 100, 200, 400):
        ks = [k for k in d if k[1] == n and "AVE-s4e36" in d[k] and "AV-s4" in d[k]]
        x = np.array([d[k]["AVE-s4e36"]["auc30"] - d[k]["AV-s4"]["auc30"] for k in ks])
        p = wilcoxon(x).pvalue if np.any(x != 0) else 1.0
        h26.append(x.mean() >= 0)
        y = np.array([d[k]["AVEK-s4e36k10"]["auc30"] - d[k]["AV-s4"]["auc30"] for k in ks if "AVEK-s4e36k10" in d[k]])
        print(f"N={n}: AVE − AV-s4 mean {x.mean():+.2f} (wins {(x > 0).sum()}/{len(x)}, p={p:.3f}); "
              f"AVEK − AV-s4 mean {y.mean():+.2f} (wins {(y > 0).sum()}/{len(y)})")
    print("H26 (AVE ≥ AV-s4 on average at every N):", all(h26), h26)
    h27, h28 = [], []
    for n in (100, 200):
        ks = [k for k in d if k[1] == n and "AVE-s4e36" in d[k] and "B1" in d[k]]
        dl = {k[0]: d[k]["AVE-s4e36"]["auc30"] - d[k]["B1"]["auc30"] for k in ks}
        h27.append(np.mean(list(dl.values())) >= -1.0)
        h28.append(all(v >= -2.0 for s, v in dl.items() if s != SEEN))
        print(f"N={n}: AVE − B1 per sequence {({s: round(v, 1) for s, v in dl.items()})}, mean {np.mean(list(dl.values())):+.2f}")
    print("H27 (AVE − B1 mean ≥ −1.0 at N=100, 200):", all(h27), h27)
    print("H28 (AVE within 2 of B1 on every sequence except fr1_360):", all(h28), h28)
    h29 = []
    for n in (100, 200):
        k = (SEEN, n)
        b = d[k]["B1"]["auc30"]
        drops = {c: round(d[k][c]["auc30"] - b, 1) for c in ("AVE-s4e36", "AVEK-s4e36k10", "K-r2k10", "AV-s4")}
        h29.append(drops["AVEK-s4e36k10"] > drops["AVE-s4e36"] and drops["K-r2k10"] > drops["AVE-s4e36"])
        print(f"fr1_360 N={n}: drop vs B1 {drops}")
    print("H29 (keyframe configs drop less than AVE on fr1_360, exploratory):", all(h29), h29)


if __name__ == "__main__":
    main()
