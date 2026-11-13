"""Validation of the full-attention band (results/band_plan.md): tables + pre-registered checks H30-H33.

    python analysis/aggregate_band.py
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
CONFIGS = ["B1", "AV-s4", "AVE-s4e36", "AVEK-s4e36k10", "AVEB-s4e36f14", "AVEKB-s4e36k10f14"]
SHORT = ["B1", "AV-s4", "AVE", "AVEK", "AVEB", "AVEKB"]
ROT = {"fr1_rpy", "fr1_plant", "fr1_teddy", "fr2_360_hemisphere"}


def main():
    d = defaultdict(dict)
    for f in sorted(R.glob("val[def]/*.jsonl")):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                d[(r["scene"], r["frames"])][r["config"]] = r
    mean = {}
    for n in (100, 200):
        ks = sorted(k for k in d if k[1] == n)
        print(f"\n#### N = {n}\n")
        print("| sequence | " + " | ".join(SHORT) + " |")
        print("|---|" + "---|" * len(SHORT))
        for k in ks:
            print(f"| {k[0]} | " + " | ".join(f"{d[k][c]['auc30']:.1f}" if c in d[k] else "–" for c in CONFIGS) + " |")
        for c in CONFIGS:
            mean[(c, n)] = (np.mean([d[k][c]["auc30"] for k in ks]), np.mean([d[k][c]["time"] for k in ks]),
                            np.mean([d[k][c]["chamfer"] for k in ks]), len(ks))
        print("| **mean** | " + " | ".join(f"**{mean[(c, n)][0]:.1f}**" for c in CONFIGS) + " |")
        print("| time (s) | " + " | ".join(f"{mean[(c, n)][1]:.0f}" for c in CONFIGS) + " |")
        print("| Chamfer | " + " | ".join(f"{mean[(c, n)][2]:.3f}" for c in CONFIGS) + " |")

    def diff(a, b, n, only=None):
        ks = [k for k in d if k[1] == n and (only is None or k[0] in only)]
        x = np.array([d[k][a]["auc30"] - d[k][b]["auc30"] for k in ks])
        p = wilcoxon(x).pvalue if np.any(x != 0) else 1.0
        return x, p

    print("\n#### Pre-registered checks\n")
    res = {}
    for name, a, b, thr in (("H30", "AVEB-s4e36f14", "AVE-s4e36", 1.0), ("H31", "AVEB-s4e36f14", "AVEK-s4e36k10", 0.0),
                            ("H32", "AVEKB-s4e36k10f14", "AVEK-s4e36k10", 0.5)):
        ok = []
        for n in (100, 200):
            x, p = diff(a, b, n)
            ok.append(x.mean() >= thr)
            print(f"{name} N={n}: {a} - {b} mean {x.mean():+.2f} (wins {(x > 0).sum()}/{len(x)}, Wilcoxon p={p:.3f}), "
                  f"needs >= {thr:+.1f}")
        res[name] = all(ok)
        print(f"{name}: {all(ok)}\n")
    ok = []
    for n in (100, 200):
        ks = [k for k in d if k[1] == n and k[0] in ROT]
        gap = np.mean([d[k]["B1"]["auc30"] - d[k]["AVEK-s4e36k10"]["auc30"] for k in ks])
        gain = np.mean([d[k]["AVEKB-s4e36k10f14"]["auc30"] - d[k]["AVEK-s4e36k10"]["auc30"] for k in ks])
        frac = gain / gap if gap > 0 else float("nan")
        ok.append(gap > 0 and frac >= 0.5)
        print(f"H33 N={n}: rotation sequences, AVEK gap to B1 {gap:.2f}, AVEKB gain {gain:+.2f} -> {frac:.0%} closed")
    res["H33"] = all(ok)
    print(f"H33: {all(ok)}\n")
    for n in (100, 200):
        print(f"N={n} speed-up vs B1: " + ", ".join(
            f"{s} {mean[('B1', n)][1] / mean[(c, n)][1]:.2f}x" for c, s in zip(CONFIGS[1:], SHORT[1:])))
    print("\nsummary:", res)


if __name__ == "__main__":
    main()
