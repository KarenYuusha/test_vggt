"""Separate check of AVEKBU-f16u10 on fresh data, and AVU-u5 on 7-Scenes (results/combo_plan.md): H43-H46.

    python analysis/aggregate_combo.py
"""
import numpy as np
from scipy.stats import wilcoxon

from aggregate_kfx import AVEK, F16, FU, U5, cells, diff, load, t200, table

CFG = ["B1", AVEK, F16, U5, FU]


def holm(ps):
    order = np.argsort(ps)
    adj, run = np.empty(len(ps)), 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def main():
    tum = load("cmb[lmn]*/*.jsonl")
    s7 = load("cmb[st]*/*.jsonl")
    for name, d in (("6 new TUM sequences", tum), ("4 new 7-Scenes sequences", s7)):
        if d:
            print(f"#### {name}")
            table(d, CFG)
            for c in CFG[1:]:
                print(f"speed-up vs B1 at N=200: {c} {t200(d, 'B1') / t200(d, c):.2f}x")
            print()
    res, ps = {}, {}
    if tum:
        x = diff(tum, FU, F16)
        x2 = diff(tum, FU, F16, 200)
        ps["H43w"] = wilcoxon(x2, alternative="greater").pvalue if np.any(x2 != 0) else 1.0
        res["H43"] = bool(x.mean() >= 0.5)
        res["H43w"] = bool(ps["H43w"] < 0.05)
        print(f"H43: f16u10 - f16n3 on TUM {x.mean():+.2f} over {len(x)} cells, wins {(x > 0).sum()} (needs >= +0.50)")
        print(f"H43w: N=200, {len(x2)} sequences {np.round(x2, 1)}, one-sided Wilcoxon p={ps['H43w']:.4f}")
        y = diff(tum, U5, F16)
        print(f"(reference) AVU-u5 - f16n3 on TUM {y.mean():+.2f}; AVU-u5 - AVEK {diff(tum, U5, AVEK).mean():+.2f}")
    if s7:
        x = diff(s7, FU, F16)
        y = diff(s7, U5, F16)
        res["H44"] = bool(x.mean() >= -0.3)
        res["H45"] = bool(y.mean() >= -0.5)
        print(f"H44: f16u10 - f16n3 on 7-Scenes {x.mean():+.2f} over {len(x)} cells (needs >= -0.30)")
        print(f"H45: AVU-u5 - f16n3 on 7-Scenes {y.mean():+.2f} over {len(y)} cells (needs >= -0.50)")
        print(f"(reference) AVU-u5 - AVEK on 7-Scenes {diff(s7, U5, AVEK).mean():+.2f}")
    if tum and s7:
        both = {**tum, **s7}
        x = diff(both, FU, F16, 200)
        ps["H46"] = wilcoxon(x, alternative="greater").pvalue
        res["H46"] = bool(ps["H46"] < 0.05)
        print(f"H46: pooled N=200, {len(x)} sequences, f16u10 - f16n3 mean {x.mean():+.2f}, wins {(x > 0).sum()}, "
              f"one-sided Wilcoxon p={ps['H46']:.4f}")
        allp = {"H40w (kfx round)": 0.03125, **ps}
        adj = holm(np.array(list(allp.values())))
        print("Holm over the round's tests: " + ", ".join(f"{k} p={v:.4f} -> {a:.4f}" for (k, v), a in
                                                           zip(allp.items(), adj)))
    print("\nsummary:", res)


if __name__ == "__main__":
    main()
