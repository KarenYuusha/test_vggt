"""Uniform-in-time keyframes on long sequences, N=400/800, low-memory forward (results/longkf_plan.md): H47-H52.

    cd analysis && python aggregate_longkf.py
"""
import numpy as np
from scipy.stats import wilcoxon

from aggregate_combo import holm
from aggregate_kfx import AVEK, F16, FU, U5, cells, diff, load

AVE, C40 = "AVE-s4e36", "AVU-c40"
CFG = ["B1", AVE, AVEK, F16, U5, FU, C40]
NS = (400, 800)


def tmean(d, c, n):
    ks = cells(d, ["B1", c], n)  # same sequences for every ratio
    return np.mean([d[k][c]["time"] for k in ks]) if ks else float("nan")


def table(d):
    cfgs = [c for c in CFG if any(c in v for v in d.values())]
    for n in NS:
        ks = sorted(k for k in d if k[1] == n)
        if not ks:
            continue
        print(f"\nN = {n} (AUC@30; '-' = not run)\n")
        print("| sequence | frames used | " + " | ".join(cfgs) + " |")
        print("|---|---|" + "---|" * len(cfgs))
        for k in ks:
            used = next(iter(d[k].values())).get("n_used", n)
            print(f"| {k[0]} | {used} | " + " | ".join(f"{d[k][c]['auc30']:.1f}" if c in d[k] else "-"
                                                     for c in cfgs) + " |")
        full = cells(d, cfgs, n)
        if full:
            print(f"| **mean ({len(full)} complete)** | | " + " | ".join(
                f"**{np.mean([d[k][c]['auc30'] for k in full]):.1f}**" for c in cfgs) + " |")
            print("| time (s) | | " + " | ".join(f"{np.mean([d[k][c]['time'] for k in full]):.0f}" for c in cfgs) + " |")
            print("| peak GB | | " + " | ".join(f"{max(d[k][c]['peak_gb'] for k in full):.2f}" for c in cfgs) + " |")
            print("| Chamfer | | " + " | ".join(f"{np.mean([d[k][c]['chamfer'] for k in full]):.3f}" for c in cfgs)
                  + " |")


def main():
    d = load("lkf*/*.jsonl")
    if not d:
        print("no results yet")
        return
    table(d)
    print()
    for n in NS:
        print(f"speed-up vs B1 at N={n}: " + ", ".join(f"{c} {tmean(d, 'B1', n) / tmean(d, c, n):.2f}x"
                                                     for c in CFG[1:]))
    res = {}
    x = diff(d, U5, AVEK)
    res["H47"] = bool(x.mean() >= 0.5)
    print(f"\nH47: AVU-u5 - AVEK {x.mean():+.2f} over {len(x)} cells, wins {(x > 0).sum()} (needs >= +0.50)")
    x8 = diff(d, U5, AVEK, 800)
    p47 = wilcoxon(x8, alternative="greater").pvalue if np.any(x8 != 0) else 1.0
    res["H47w"] = bool(p47 < 0.05)
    print(f"H47w: N=800, {len(x8)} sequences {np.round(x8, 1)}, one-sided Wilcoxon p={p47:.4f}")
    x = diff(d, FU, F16)
    res["H48"] = bool(x.mean() >= 0.5)
    print(f"H48: f16u10 - f16n3 {x.mean():+.2f} over {len(x)} cells, wins {(x > 0).sum()} (needs >= +0.50)")
    x = diff(d, FU, "B1")
    res["H49"] = bool(x.mean() >= -1.0)
    print(f"H49: f16u10 - B1 {x.mean():+.2f} over {len(x)} cells (needs >= -1.00)")
    for h, c, thr in (("H50a", AVE, 4.5), ("H50b", U5, 3.0), ("H50c", FU, 2.5)):
        sp = tmean(d, "B1", 800) / tmean(d, c, 800)
        res[h] = bool(sp >= thr)
        print(f"{h}: N=800 B1/{c} time {sp:.2f}x over {len(cells(d, ['B1', c], 800))} sequences (needs >= {thr})")
    x = diff(d, C40, U5)
    tr = tmean(d, C40, 800) / tmean(d, U5, 800)
    res["H51"] = bool(x.mean() >= -0.3 and tr <= 0.8)
    print(f"H51: AVU-c40 - AVU-u5 {x.mean():+.2f} over {len(x)} cells (needs >= -0.30); "
          f"time ratio at N=800 {tr:.2f} (needs <= 0.80)")
    x = diff(d, C40, AVE)
    tr = tmean(d, C40, 800) / tmean(d, AVE, 800)
    res["H52"] = bool(x.mean() >= 0.5 and tr <= 1.15)
    print(f"H52: AVU-c40 - AVE {x.mean():+.2f} over {len(x)} cells, wins {(x > 0).sum()} (needs >= +0.50); "
          f"time ratio at N=800 {tr:.2f} (needs <= 1.15)")
    for c in CFG[1:]:
        print(f"(reference) {c} - B1: N=400 {diff(d, c, 'B1', 400).mean():+.2f}, "
              f"N=800 {diff(d, c, 'B1', 800).mean():+.2f}")

    ks = cells(d, CFG, 800)
    if ks:
        b1 = np.mean([d[k]["B1"]["auc30"] for k in ks])
        ok = [(np.mean([d[k][c]["time"] for k in ks]), c) for c in CFG[1:]
              if np.mean([d[k][c]["auc30"] for k in ks]) >= b1 - 1.0]
        best = min(ok)[1] if ok else max(CFG[1:], key=lambda c: np.mean([d[k][c]["auc30"] for k in ks]))
        print(f"\nlong-sequence pick (fastest within 1.0 of B1 at N=800, {len(ks)} sequences): "
              f"{best}{'' if ok else ' (none within 1.0; highest AUC)'}")
    allp = {"H40w": 0.03125, "H43w": 0.109375, "H46": 0.1162109375, "H47w": p47}
    adj = holm(np.array(list(allp.values())))
    print("Holm: " + ", ".join(f"{k} p={v:.4f} -> {a:.4f}" for (k, v), a in zip(allp.items(), adj)))
    print("\nsummary:", res)


if __name__ == "__main__":
    main()
