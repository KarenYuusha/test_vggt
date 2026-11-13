"""Diagnose the office seq-06 failure: separate mass correction (alpha) from keyframe-descriptor dedup, and find which
frames drift from the full-attention output.

    python analysis/diag_office.py <seq_dir> [N ...]
Writes results/diag/<scene>_<seq>.jsonl (one row per config and N, plus per-frame rotation error vs B1).
"""
import gc
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import numpy as np  # noqa: E402

from tfvggt.core import build_model, configure  # noqa: E402
from tfvggt.evaluation import _rot_angle, evaluate, fidelity, load_sequence, predict  # noqa: E402

CONFIGS = {
    "B1": dict(r=1),
    "E1": dict(r=3, alpha=0.0, dedup=False),   # = E1-all on Kaggle
    "E1d": dict(r=3, alpha=0.0, dedup=True),
    "E2n": dict(r=3, alpha=1.0, dedup=False),
    "E2": dict(r=3, alpha=1.0, dedup=True),    # = E2-all on Kaggle
    "E2h": dict(r=3, alpha=0.5, dedup=True),
    # extra full-resolution keyframes picked by FlashVGGT's k-means on DINO frame tokens (S // k clusters + frame 0)
    "E1k10": dict(r=3, alpha=0.0, dedup=False, keyframe_every=10),
    "E2k10": dict(r=3, alpha=1.0, dedup=True, keyframe_every=10),
    "E1k5": dict(r=3, alpha=0.0, dedup=False, keyframe_every=5),
    "E2k5": dict(r=3, alpha=1.0, dedup=True, keyframe_every=5),
    "E1r2": dict(r=2, alpha=0.0, dedup=False),
    "E2r2": dict(r=2, alpha=1.0, dedup=True),
    "E1r2k10": dict(r=2, alpha=0.0, dedup=False, keyframe_every=10),
    "E1r4k5": dict(r=4, alpha=0.0, dedup=False, keyframe_every=5),
}
# AVGGT reproduction and neighbourhood resolution (shared with tfvggt.configs)
from tfvggt.configs import CONFIGS as RUN_CONFIGS  # noqa: E402
CONFIGS.update({k: kw for k, (w, kw) in RUN_CONFIGS.items() if k.startswith(("AV", "NB", "G-", "Q-")) and w == "vggt"})  # AV* covers AVS/AVES/AVK/AVEK
if os.environ.get("DIAG_CONFIGS"):
    CONFIGS = {k: CONFIGS[k] for k in ["B1"] + os.environ["DIAG_CONFIGS"].split()}


def frame_rot_err(w2c, ref_w2c):
    """Rotation error (deg) of the pose of every frame relative to frame 0, against the B1 prediction."""
    rel = w2c @ np.linalg.inv(w2c[0])
    rref = ref_w2c @ np.linalg.inv(ref_w2c[0])
    return _rot_angle(rel[:, :3, :3] @ np.transpose(rref[:, :3, :3], (0, 2, 1)))


def main():
    seq = Path(sys.argv[1]).resolve()
    frames = [int(x) for x in sys.argv[2:]] or [25]
    out = ROOT / "results" / "diag" / f"{seq.parent.name}_{seq.name}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    model = build_model("vggt")
    model.lowmem = bool(os.environ.get("DIAG_LOWMEM"))  # streaming forward: no VRAM spill, so local times are usable
    for n in frames:
        images, gt_depth, gt_c2w, K = load_sequence(seq, n)
        ref = None
        for name, kw in CONFIGS.items():
            configure(model, **kw)
            pred = predict(model, images)
            m = evaluate(pred, gt_depth, gt_c2w, K)
            row = dict(config=name, frames=n, **{k: float(v) for k, v in m.items()})
            if name == "B1":
                ref = pred
            else:
                row.update({k: float(v) for k, v in fidelity(pred, ref).items()})
                row["frame_rot_err"] = [round(float(e), 2) for e in frame_rot_err(pred["w2c"], ref["w2c"])]
            with open(out, "a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{name:7s} N={n} t={m['time']:.1f}s AUC30={m['auc30']:.1f} ATE={m['ate']:.3f} CD={m['chamfer']:.3f} "
                  f"fid={row.get('fid_pose', float('nan')):.1f} "
                  f"maxrot={max(row.get('frame_rot_err', [0])):.1f}", flush=True)
            gc.collect()


if __name__ == "__main__":
    main()
