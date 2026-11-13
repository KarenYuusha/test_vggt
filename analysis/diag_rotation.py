"""Where do compressed configs lose pose accuracy on rotation-heavy sequences? (results/rotation_plan.md, D1-D3)

    python analysis/diag_rotation.py
Reads predicted w2c saved by `tfvggt run --save-poses` (results/kaggle/rot*/poses/*.npy) and the ground truth in
data/tum/<scene>/<seq>.
"""
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
K = ROOT / "results" / "kaggle"
CONFIGS = ["AV-s4", "AVEK-s4e36k10", "AVEKB-f16n3", "ABL-e36-Lfull", "ABL-Efull-s4k10"]
SHORT = {"AV-s4": "AVGGT", "AVEK-s4e36k10": "AVEK", "AVEKB-f16n3": "f16n3", "ABL-e36-Lfull": "early grid only",
         "ABL-Efull-s4k10": "late compr. only"}
BINS = [(0, 30), (30, 90), (90, 181)]
TH = np.arange(1, 31)


def rot_angle(R):
    return np.degrees(np.arccos(np.clip((np.trace(R, axis1=-2, axis2=-1) - 1) / 2, -1, 1)))


def gt_c2w(scene, seq, n):
    d = ROOT / "data" / "tum" / scene / seq
    poses = sorted(d.glob("*.pose.txt"))
    ids = np.unique(np.linspace(0, len(poses) - 1, n).round().astype(int))
    return np.stack([np.loadtxt(poses[i]) for i in ids])


def pair_errors(w2c, gt):
    """Per pair (i<j): max(rotation error, translation-direction error) as in tfvggt.evaluation.pose_metrics, and GT rotation."""
    gw = np.linalg.inv(gt)
    i, j = np.triu_indices(len(gw), 1)
    rp, rg = w2c[j] @ np.linalg.inv(w2c[i]), gw[j] @ np.linalg.inv(gw[i])
    r_err = rot_angle(rp[:, :3, :3] @ np.transpose(rg[:, :3, :3], (0, 2, 1)))
    tp, tg = rp[:, :3, 3], rg[:, :3, 3]
    cos = (tp * tg).sum(1) / (np.linalg.norm(tp, axis=1) * np.linalg.norm(tg, axis=1) + 1e-9)
    t_err = np.degrees(np.arccos(np.clip(np.abs(cos), -1, 1)))
    return np.maximum(r_err, t_err), rot_angle(rg[:, :3, :3]), i, j


def score(err):
    """Per-pair contribution to AUC@30 (mean over thresholds 1..30 of err < th), x100."""
    return (err[:, None] < TH[None]).mean(1) * 100


def main():
    poses = {}
    for f in K.glob("rot*/poses/*.npy"):
        c, scene, seq, n = f.stem.split("__")
        poses[(c, scene, seq, int(n))] = np.load(f).astype(np.float64)
    seqs = sorted({k[1:] for k in poses if k[0] == "B1"})
    auc = defaultdict(dict)
    bins = defaultdict(lambda: defaultdict(list))  # (config) -> bin -> per-seq deficit
    conc = defaultdict(list)
    corr = defaultdict(list)
    kfp = ROOT / "results" / "diag" / "keyframes_rot.json"  # AVEK k-means keyframes, captured locally (see rotation_plan)
    kfs = json.loads(kfp.read_text()) if kfp.exists() else {}
    print("#### D1: AUC@30 deficit vs B1 per sequence\n")
    print("| sequence | N | B1 | " + " | ".join(SHORT[c] for c in CONFIGS) + " |")
    print("|---|---|---|" + "---|" * len(CONFIGS))
    for scene, seq, n in seqs:
        gt = gt_c2w(scene, seq, n)
        e0, ang, i, j = pair_errors(poses[("B1", scene, seq, n)], gt)
        s0 = score(e0)
        auc[(scene, n)]["B1"] = s0.mean()
        cells = []
        for c in CONFIGS:
            if (c, scene, seq, n) not in poses:
                cells.append("–")
                continue
            e, _, _, _ = pair_errors(poses[(c, scene, seq, n)], gt)
            s = score(e)
            auc[(scene, n)][c] = s.mean()
            cells.append(f"{s.mean() - s0.mean():+.1f}")
            d = s0 - s  # per-pair deficit
            for b, (lo, hi) in enumerate(BINS):
                m = (ang >= lo) & (ang < hi)
                bins[c][b].append((d[m].mean() if m.any() else np.nan, m.mean()))
            # D3: share of the total deficit carried by pairs touching the worst 10% frames (by per-frame deficit)
            S = len(gt)
            fd = np.zeros(S)
            np.add.at(fd, i, d)
            np.add.at(fd, j, d)
            cnt = np.zeros(S)
            np.add.at(cnt, i, 1)
            np.add.at(cnt, j, 1)
            b1f = np.zeros(S)
            np.add.at(b1f, i, s0)
            np.add.at(b1f, j, s0)
            gw = np.linalg.inv(gt)
            step = np.r_[0, rot_angle(gw[1:, :3, :3] @ np.transpose(gw[:-1, :3, :3], (0, 2, 1)))]
            kd = np.full(S, np.nan)
            if f"{scene}__{n}" in kfs:  # D4: GT rotation from each frame to its nearest keyframe
                kf = np.array(kfs[f"{scene}__{n}"])
                Rk = gw[kf, :3, :3]
                kd = rot_angle(gw[:, None, :3, :3] @ np.transpose(Rk, (0, 2, 1))[None]).min(1)
                kd[kf] = np.nan  # keyframes themselves
            ok = ~np.isnan(kd)
            corr[c].append((spearmanr(fd / cnt, b1f / cnt)[0], spearmanr(fd / cnt, step)[0],
                            spearmanr((fd / cnt)[ok], kd[ok])[0] if ok.sum() > 5 else np.nan))
            worst = np.argsort(-fd)[:max(1, S // 10)]
            touch = np.isin(i, worst) | np.isin(j, worst)
            if d.mean() >= 1.0:  # D3 only where the config loses at least 1 AUC point (the share is unstable otherwise)
                # null: same selection after shuffling the per-pair deficits (no frame structure)
                rng = np.random.default_rng(0)
                null = []
                for _ in range(20):
                    dp = rng.permutation(d)
                    fp = np.zeros(S)
                    np.add.at(fp, i, dp)
                    np.add.at(fp, j, dp)
                    wp = np.argsort(-fp)[:max(1, S // 10)]
                    tp = np.isin(i, wp) | np.isin(j, wp)
                    null.append(dp[tp].sum() / dp.sum())
                conc[c].append((d[touch].sum() / d.sum(), touch.mean(), np.mean(null)))
        print(f"| {scene} | {n} | {s0.mean():.1f} | " + " | ".join(cells) + " |")

    print("\n#### D2: mean per-pair deficit vs B1 by GT rotation between the two frames (AUC points)\n")
    print("| config | " + " | ".join(f"{lo}–{min(hi, 180)}° (share of pairs)" for lo, hi in BINS) + " |")
    print("|---|" + "---|" * len(BINS))
    for c in CONFIGS:
        print(f"| {SHORT[c]} | " + " | ".join(
            f"{np.nanmean([x for x, _ in bins[c][b]]):+.1f} ({np.mean([w for _, w in bins[c][b]]):.0%})"
            for b in range(len(BINS))) + " |")

    print("\n#### D3: share of the deficit in pairs touching the worst 10% frames (those pairs are ~19% of all)\n")
    for c in CONFIGS:
        if conc[c]:
            print(f"- {SHORT[c]}: {np.mean([a for a, _, _ in conc[c]]):.0%} of the deficit "
                  f"(pairs touching them: {np.mean([b for _, b, _ in conc[c]]):.0%}; same selection on shuffled "
                  f"deficits: {np.mean([x for _, _, x in conc[c]]):.0%}), over {len(conc[c])} cells")
    print("\n#### D3b: Spearman correlation of the per-frame deficit with (a) B1's per-frame score, (b) GT rotation to "
          "the previous sampled frame\n")
    for c in CONFIGS:
        if corr[c]:
            print(f"- {SHORT[c]}: (a) {np.mean([x[0] for x in corr[c]]):+.2f}  (b) {np.mean([x[1] for x in corr[c]]):+.2f}"
                  f"  (D4: rotation to nearest keyframe) {np.nanmean([x[2] for x in corr[c]]):+.2f}"
                  f"  (mean over {len(corr[c])} cells)")
    orc = {}
    for f in K.glob("orc*/*.jsonl"):
        for line in open(f):
            if line.strip():
                r = json.loads(line)
                orc[(r["config"], r["scene"], r["frames"])] = r["auc30"]
    if orc:
        print("\n#### Oracle experiment (O1, O2): cells where AVEK loses >= 1 point vs B1\n")
        print("| sequence | N | B1 | AVEK | AVEK-rand | AVEK-oracle | recovered |")
        print("|---|---|---|---|---|---|---|")
        rec, gap = [], []
        for (scene, n), a in sorted(auc.items()):
            if ("AVEK-oracle", scene, n) not in orc or "AVEK-s4e36k10" not in a:
                continue
            b, k = a["B1"], a["AVEK-s4e36k10"]
            o, rd = orc[("AVEK-oracle", scene, n)], orc.get(("AVEK-rand", scene, n), np.nan)
            mark = ""
            if b - k >= 1:
                rec.append((o - k) / (b - k))
                gap.append(o - rd)
            else:
                mark = " (excluded)"
            print(f"| {scene}{mark} | {n} | {b:.1f} | {k:.1f} | {rd:.1f} | {o:.1f} | "
                  f"{(o - k) / (b - k):.0%} |" if b - k >= 1 else f"| {scene}{mark} | {n} | {b:.1f} | {k:.1f} | {rd:.1f} | {o:.1f} | – |")
        if rec:
            print(f"\nO1: mean recovered {np.mean(rec):.0%} over {len(rec)} cells (needs >= 50%) -> {np.mean(rec) >= 0.5}")
            print(f"O2: mean oracle - rand {np.mean(gap):+.2f} (needs >= +1.0) -> {np.mean(gap) >= 1.0}")
    rows = [json.loads(line) for f in K.glob("rot*/*.jsonl") for line in open(f) if line.strip()]
    chk = [(r["config"], r["scene"], r["frames"], r["auc30"]) for r in rows]
    bad = [(c, s, n, a, auc[(s, n)].get(c)) for c, s, n, a in chk if c in auc[(s, n)] and abs(auc[(s, n)][c] - a) > 0.05]
    print(f"\ncheck vs kernel AUC: {len(chk) - len(bad)}/{len(chk)} agree" + (f", differ: {bad[:3]}" if bad else ""))


if __name__ == "__main__":
    main()
