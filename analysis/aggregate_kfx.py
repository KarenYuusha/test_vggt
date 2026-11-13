"""Uniform-in-time extra keyframes (results/kfx_plan.md): selection rule on development data, checks H40-H42.

    python analysis/aggregate_kfx.py
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
AVEK, F16 = "AVEK-s4e36k10", "AVEKB-f16n3"
U10, U5, FU = "AVEKU-u10", "AVU-u5", "AVEKBU-f16u10"
SHOW = ["B1", AVEK, F16, "AVEK-rand", U10, U5, FU]
DEV_SCENES = {"fr1_360", "fr1_room", "fr1_rpy", "fr1_plant", "fr1_teddy", "fr2_360_hemisphere"}


def load(*patterns, scenes=None):
    d = defaultdict(dict)
    for pat in patterns:
        for f in sorted(R.glob(pat)):
            for line in open(f):
                if line.strip():
                    r = json.loads(line)
                    if scenes is None or r["scene"] in scenes:
                        d[(f"{r['scene']}/{r.get('seq', '')}".rstrip("/"), r["frames"])][r["config"]] = r
    return d


def cells(d, cfgs, n=None):
    return sorted(k for k in d if all(c in d[k] for c in cfgs) and (n is None or k[1] == n))


def diff(d, a, b, n=None):
    return np.array([d[k][a]["auc30"] - d[k][b]["auc30"] for k in cells(d, [a, b], n)])


def t200(d, c):
    ks = cells(d, [c], 200)
    return np.mean([d[k][c]["time"] for k in ks]) if ks else float("nan")


def table(d, cfgs):
    cfgs = [c for c in cfgs if any(c in v for v in d.values())]
    for n in (100, 200):
        ks = cells(d, cfgs, n)
        if not ks:
            continue
        print(f"\nN = {n}\n")
        print("| sequence | " + " | ".join(cfgs) + " |")
        print("|---|" + "---|" * len(cfgs))
        for k in ks:
            print(f"| {k[0]} | " + " | ".join(f"{d[k][c]['auc30']:.1f}" for c in cfgs) + " |")
        print("| **mean** | " + " | ".join(f"**{np.mean([d[k][c]['auc30'] for k in ks]):.1f}**" for c in cfgs) + " |")
        print("| time (s) | " + " | ".join(f"{np.mean([d[k][c]['time'] for k in ks]):.0f}" for c in cfgs) + " |")


def main():
    dev = load("rot*/*.jsonl", "orc*/*.jsonl", "kfx[abdef]/*.jsonl", scenes=DEV_SCENES)
    print("#### Step 1: development data (6 rotation-heavy TUM sequences x N=100, 200)")
    table(dev, SHOW)
    print("\n| config | gain vs AVEK (cells) | time N=200 (s) |\n|---|---|---|")
    g = {}
    for c in [F16, "AVEK-rand", U10, U5, FU]:
        x = diff(dev, c, AVEK)
        g[c] = (x.mean() if len(x) else float("nan"), len(x))
        print(f"| {c} | {g[c][0]:+.2f} ({g[c][1]}) | {t200(dev, c):.0f} |")
    ok = [(g[c][0], c) for c in (U10, U5) if g[c][1] == 12 and g[c][0] >= 0.5]
    cstar = max(ok)[1] if ok else None
    keep_fu = g[FU][1] == 12 and g[F16][1] == 12 and g[FU][0] - g[F16][0] >= 0.5
    print(f"\nC* = {cstar}; combined kept = {keep_fu} (gain(f16u10) - gain(f16n3) = {g[FU][0] - g[F16][0]:+.2f})")

    val = load("kfx[ijk]/*.jsonl")
    if not val:
        return
    print("\n#### Step 2: 6 unseen TUM sequences")
    table(val, ["B1", AVEK, F16, U10, U5, FU])
    res = {}
    for c in (U10, U5, FU):
        x, y = diff(val, c, AVEK), diff(val, c, F16)
        print(f"{c}: vs AVEK {x.mean():+.2f} ({len(x)} cells, wins {(x > 0).sum()}), vs f16n3 {y.mean():+.2f}, "
              f"time N=200 {t200(val, c):.0f} s")
    if cstar:
        x = diff(val, cstar, AVEK)
        x2 = diff(val, cstar, AVEK, 200)
        p = wilcoxon(x2, alternative="greater").pvalue if np.any(x2 != 0) else 1.0
        y = diff(val, cstar, F16)
        tr = t200(val, cstar) / t200(val, F16)
        res["H40"] = bool(x.mean() >= 0.5)
        res["H40w"] = bool(p < 0.05)
        res["H41"] = bool(y.mean() >= 0 and tr <= 1.05)
        print(f"\nH40: {cstar} - AVEK {x.mean():+.2f} over {len(x)} cells (needs >= +0.50)")
        print(f"H40w: N=200, {len(x2)} sequences, mean {x2.mean():+.2f}, wins {(x2 > 0).sum()}/{len(x2)}, "
              f"one-sided Wilcoxon p={p:.4f}")
        print(f"H41: {cstar} - f16n3 {y.mean():+.2f}; time ratio vs f16n3 at N=200 {tr:.2f}")
    else:
        res["H40"] = res["H40w"] = res["H41"] = "n/a (no C*)"
    if keep_fu:
        y = diff(val, FU, F16)
        res["H42"] = bool(y.mean() >= 0.5)
        print(f"H42: f16u10 - f16n3 {y.mean():+.2f} over {len(y)} cells (needs >= +0.50)")
    else:
        res["H42"] = "n/a (combined variant dropped in step 1)"
    for c in (AVEK, F16, U10, U5, FU):
        print(f"speed-up vs B1 at N=200: {c} {t200(val, 'B1') / t200(val, c):.2f}x")
    print("\nsummary:", res)


if __name__ == "__main__":
    main()
