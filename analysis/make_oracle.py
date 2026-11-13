"""Extra-keyframe lists for the oracle experiment (results/rotation_plan.md): per (scene, N), the S//10 non-keyframe
frames with the largest AVEK deficit vs B1 (ground truth), and as many random non-keyframe frames (seed 0).

    python analysis/make_oracle.py   ->  src/tfvggt/assets/oracle_keyframes.json
"""
import json
from pathlib import Path

import numpy as np

from diag_rotation import K, ROOT, gt_c2w, pair_errors, score

kfs = json.loads((ROOT / "results" / "diag" / "keyframes_rot.json").read_text())
out = {"oracle": {}, "rand": {}}
rng = np.random.default_rng(0)
for f in sorted(K.glob("rot*/poses/B1__*.npy")):
    _, scene, seq, n = f.stem.split("__")
    gt = gt_c2w(scene, seq, int(n))
    S = len(gt)
    e0, _, i, j = pair_errors(np.load(f).astype(float), gt)
    e, _, _, _ = pair_errors(np.load(f.with_name(f"AVEK-s4e36k10__{scene}__{seq}__{n}.npy")).astype(float), gt)
    d = score(e0) - score(e)
    fd = np.zeros(S)
    np.add.at(fd, i, d)
    np.add.at(fd, j, d)
    kf = set(kfs[f"{scene}__{n}"])
    cand = [x for x in np.argsort(-fd).tolist() if x not in kf]
    key = f"{scene}__{n}"
    out["oracle"][key] = sorted(cand[:S // 10])
    out["rand"][key] = sorted(rng.choice([x for x in range(S) if x not in kf], S // 10, replace=False).tolist())
    print(key, "oracle", out["oracle"][key])
ROOT / "src" / "tfvggt" / "assets" / "oracle_keyframes.json".write_text(json.dumps(out))
