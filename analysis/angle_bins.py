"""Per-frame pose drift vs B1, binned by the ground-truth rotation between each frame and frame 0.

    python analysis/angle_bins.py <seq_dir> [configs ...]
Reads results/diag/<scene>_<seq>.jsonl (written by analysis/diag_office.py, which stores per-frame rotation error vs B1).
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
from tfvggt.evaluation import _rot_angle  # noqa: E402

BINS = [(0, 60), (60, 105), (105, 181)]


def frame_angles(seq, n):
    """Rotation angle (deg) of every sampled frame w.r.t. frame 0, same sampling as tfvggt.evaluation.load_sequence."""
    poses = sorted(seq.glob("*.pose.txt"))
    idx = np.unique(np.linspace(0, len(poses) - 1, n).round().astype(int))
    c2w = np.stack([np.loadtxt(poses[i]) for i in idx])
    rel = np.linalg.inv(c2w[0])[None] @ c2w
    return _rot_angle(rel[:, :3, :3])


def main():
    seq = Path(sys.argv[1]).resolve()
    configs = sys.argv[2:] or ["AV-s4", "AV-s4-g0", "AVE-s4e36", "AVK-s9k10", "AVEK-s9e36k10"]
    rows = [json.loads(line) for line in open(ROOT / "results" / "diag" / f"{seq.parent.name}_{seq.name}.jsonl")]
    last = {(r["config"], r["frames"]): r for r in rows if "frame_rot_err" in r}  # latest run wins
    for n in sorted({r["frames"] for r in rows}):
        ang = frame_angles(seq, n)
        counts = [int(((ang >= lo) & (ang < hi)).sum()) for lo, hi in BINS]
        print(f"\nN={n}  frames per bin " + ", ".join(f"{lo}-{hi}°: {c}" for (lo, hi), c in zip(BINS, counts)))
        print("| config | " + " | ".join(f"{lo}–{min(hi, 180)}°" for lo, hi in BINS) + " |")
        print("|---|" + "---|" * len(BINS))
        for c in configs:
            if (c, n) not in last:
                continue
            err = np.array(last[(c, n)]["frame_rot_err"])
            cells = [f"{err[(ang >= lo) & (ang < hi)].mean():.1f}" if ((ang >= lo) & (ang < hi)).any() else "–"
                     for lo, hi in BINS]
            print(f"| {c} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
