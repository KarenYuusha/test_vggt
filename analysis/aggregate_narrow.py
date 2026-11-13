"""Cheaper bands + AVEKB on unseen 7-Scenes (results/narrow_plan.md): selection rule, tables, checks H34-H37.

    python analysis/aggregate_narrow.py
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
AVEK, AVEKB = "AVEK-s4e36k10", "AVEKB-s4e36k10f14"
VARIANTS = ["AVEKB-f15n3", "AVEKB-f14n3", "AVEKB-f16n3", "AVEKB-g12"]
SEVEN = ["B1", "AV-s4", AVEK, AVEKB] + VARIANTS


def load(pattern):
    d = defaultdict(dict)
    for f in sorted(R.glob(pattern)):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                d[(f"{r['scene']}/{r.get('seq', '')}".rstrip("/"), r["frames"])][r["config"]] = r
    return d


def cells(d, cfgs):
    return sorted(k for k in d if all(c in d[k] for c in cfgs))


def gain(d, v, ns=(100, 200)):
    ks = [k for k in cells(d, [v, AVEK]) if k[1] in ns]
    return np.mean([d[k][v]["auc30"] - d[k][AVEK]["auc30"] for k in ks]), len(ks)


def t200(d, c):
    return np.mean([d[k][c]["time"] for k in cells(d, [c]) if k[1] == 200])


def main():
    dev = load("val[def]/*.jsonl")  # vald/vale/valf (AVEK, AVEKB) ...
    for k, v in load("nar[def]/*.jsonl").items():  # ... + the variants
        dev[k].update(v)
    print("#### Step 1: selection on development data (6 TUM sequences x N=100, 200)\n")
    print("| config | gain vs AVEK (cells) | time N=200 (s) | cost vs AVEK (s) |")
    print("|---|---|---|---|")
    gb, _ = gain(dev, AVEKB)
    sel = []
    for v in [AVEKB] + VARIANTS:
        g, n = gain(dev, v)
        cost = t200(dev, v) - t200(dev, AVEK)
        print(f"| {v} | {g:+.2f} ({n}) | {t200(dev, v):.0f} | {cost:+.0f} |")
        if v != AVEKB and n == 12 and g >= 0.7 * gb:
            sel.append((cost, -g, v))
    vstar = min(sel)[2] if sel else None
    print(f"\nthreshold 0.7 x gain(AVEKB) = {0.7 * gb:.2f}; V* = {vstar}\n")

    s7 = load("s5[abc]/*.jsonl")
    if not s7:
        return
    print("#### Step 2: unseen 7-Scenes\n")
    for n in (100, 200):
        ks = [k for k in cells(s7, SEVEN) if k[1] == n]
        print(f"\nN = {n}\n")
        print("| sequence | " + " | ".join(SEVEN) + " |")
        print("|---|" + "---|" * len(SEVEN))
        for k in ks:
            print(f"| {k[0]} | " + " | ".join(f"{s7[k][c]['auc30']:.1f}" for c in SEVEN) + " |")
        print("| **mean** | " + " | ".join(f"**{np.mean([s7[k][c]['auc30'] for k in ks]):.1f}**" for c in SEVEN) + " |")
        print("| time (s) | " + " | ".join(f"{np.mean([s7[k][c]['time'] for k in ks]):.0f}" for c in SEVEN) + " |")

    def diff(d, a, b, n):
        ks = [k for k in cells(d, [a, b]) if k[1] == n]
        return np.array([d[k][a]["auc30"] - d[k][b]["auc30"] for k in ks])

    print("\n#### Pre-registered checks\n")
    res = {}
    for name, b, thr in (("H34", AVEK, 0.0), ("H35", "AV-s4", 0.5)):
        ok = []
        for n in (100, 200):
            x = diff(s7, AVEKB, b, n)
            p = wilcoxon(x).pvalue if np.any(x != 0) else 1.0
            ok.append(x.mean() >= thr)
            print(f"{name} N={n}: AVEKB - {b} mean {x.mean():+.2f} (wins {(x > 0).sum()}/{len(x)}, p={p:.3f}), "
                  f"needs >= {thr:+.1f}")
        res[name] = all(ok)
    if vstar:
        gs, _ = gain(s7, vstar)
        gk, _ = gain(s7, AVEKB)
        sp = t200(s7, "B1") / t200(s7, vstar)
        frac = gs / gk if gk > 0 else float("nan")
        res["H36"] = bool(gk > 0 and frac >= 0.7 and sp >= 2.2)
        print(f"H36: gain({vstar}) {gs:+.2f} vs gain(AVEKB) {gk:+.2f} -> {frac:.0%}; speed-up vs B1 at N=200 {sp:.2f}x")
    else:
        res["H36"] = "n/a (no V*)"
    pooled = load("val[def]/*.jsonl")
    pooled.update(s7)
    x = diff(pooled, AVEKB, AVEK, 200)
    p = wilcoxon(x, alternative="greater").pvalue
    res["H37"] = bool(p < 0.05)
    print(f"H37: pooled N=200, {len(x)} sequences, AVEKB - AVEK mean {x.mean():+.2f}, wins {(x > 0).sum()}/{len(x)}, "
          f"one-sided Wilcoxon p={p:.4f}")
    for c in SEVEN[1:]:
        print(f"7-Scenes N=200 speed-up vs B1: {c} {t200(s7, 'B1') / t200(s7, c):.2f}x")

    v4 = load("v[gh]/*.jsonl")
    if v4 and vstar:
        cf = ["B1", "AV-s4", AVEK, AVEKB, vstar]
        print("\n#### Extra: 4 new TUM sequences\n")
        for n in (100, 200):
            ks = [k for k in cells(v4, cf) if k[1] == n]
            print(f"\nN = {n}\n")
            print("| sequence | " + " | ".join(cf) + " |")
            print("|---|" + "---|" * len(cf))
            for k in ks:
                print(f"| {k[0]} | " + " | ".join(f"{v4[k][c]['auc30']:.1f}" for c in cf) + " |")
            print("| **mean** | " + " | ".join(f"**{np.mean([v4[k][c]['auc30'] for k in ks]):.1f}**" for c in cf) + " |")
            print("| time (s) | " + " | ".join(f"{np.mean([v4[k][c]['time'] for k in ks]):.0f}" for c in cf) + " |")
        gk, nk = gain(v4, AVEKB)
        gs, _ = gain(v4, vstar)
        res["H38a"] = bool(gk >= 0.5)
        res["H38b"] = bool(gk > 0 and gs >= 0.7 * gk)
        print(f"\nH38a: AVEKB - AVEK {gk:+.2f} over {nk} cells, needs >= +0.50")
        print(f"H38b: gain({vstar}) {gs:+.2f} vs gain(AVEKB) {gk:+.2f}" + (f" -> {gs / gk:.0%}" if gk > 0 else ""))
        print(f"speed-up vs B1 at N=200: AVEKB {t200(v4, 'B1') / t200(v4, AVEKB):.2f}x, "
              f"{vstar} {t200(v4, 'B1') / t200(v4, vstar):.2f}x")
        allun = load("val[def]/*.jsonl")
        for src in (s7, v4):
            allun.update(src)
        h39 = []
        for name, d, c in (("AVEKB, 17 unseen", allun, AVEKB),
                           (f"{vstar}, 11 sequences not used to select it (7-Scenes + 4 TUM)", {**s7, **v4}, vstar)):
            x = diff(d, c, AVEK, 200)
            p = wilcoxon(x, alternative="greater").pvalue
            h39.append(p < 0.05)
            print(f"H39 {name}: N=200 mean {x.mean():+.2f}, wins {(x > 0).sum()}/{len(x)}, one-sided p={p:.4f}")
        devx = load("nar[def]/*.jsonl")
        for k, v in load("val[def]/*.jsonl").items():
            devx[k].update(v)
        x = np.concatenate([diff(devx, vstar, AVEK, 200), diff({**s7, **v4}, vstar, AVEK, 200)])
        print(f"    ({vstar} on all 17 incl. its 6 selection sequences, biased: mean {x.mean():+.2f}, "
              f"p={wilcoxon(x, alternative='greater').pvalue:.4f})")
        res["H39"] = bool(all(h39))
    print("\nsummary:", res)


if __name__ == "__main__":
    main()
