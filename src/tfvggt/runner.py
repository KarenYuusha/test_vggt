"""Run named configurations on sequences and append one JSON line per (config, sequence, N) to <out>/<tag>.jsonl.

Resumable: rows already in the file are skipped (B1 is re-run when a later config needs it for the fidelity metrics).
"""
import gc
import json
from pathlib import Path

import numpy as np
import torch

from tfvggt.configs import BUDGET_TOKENS, CONFIGS, oracle_keyframes
from tfvggt.core import budget_r, build_model, configure
from tfvggt.evaluation import evaluate, fidelity, load_sequence, predict


def run(seqs, frames, configs, out_file, lowmem=False, save_poses=False, plan=None):
    """seqs: sequence folders (<scene>/<seq>); frames: list of N; configs: names in tfvggt.configs.CONFIGS;
    plan: optional {config: set of N} restricting which N a config runs at."""
    plan = plan or {}
    unknown = [c for c in configs if c not in CONFIGS]
    if unknown:
        raise ValueError(f"unknown configs {unknown}; see `tfvggt configs`")
    out = Path(out_file).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                done.add((r["config"], r["scene"], r.get("seq", ""), r["frames"]))
    seqs = [Path(s).resolve() for s in seqs]

    by_weights = {}
    for name in configs:
        by_weights.setdefault(CONFIGS[name][0], []).append(name)
    refs = {}  # (scene, seq, N) -> B1 prediction, for fidelity
    order = sorted(by_weights, key=lambda w: w != "vggt")  # vggt first so B1 references exist
    for weights in order:
        model = build_model(weights)
        model.lowmem = lowmem
        for seq in seqs:
            for n in frames:
                images, gt_depth, gt_c2w, K = load_sequence(seq, n)
                pH, pW = images.shape[-2] // 14, images.shape[-1] // 14
                for name in by_weights[weights]:
                    if name in plan and n not in plan[name]:
                        continue
                    key = (name, seq.parent.name, seq.name, n)
                    if key in done and not (name == "B1" and (seq.parent.name, seq.name, n) not in refs):
                        continue
                    kw = dict(CONFIGS[name][1])
                    if isinstance(kw.get("keyframe_extra"), str):
                        kw["keyframe_extra"] = oracle_keyframes(kw["keyframe_extra"], seq.parent.name, n)
                    if kw.get("r") == "budget":
                        kw["r"] = budget_r(n, BUDGET_TOKENS, pH, pW)
                    configure(model, **kw)
                    try:
                        pred = predict(model, images)
                    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
                        if "out of memory" not in str(e).lower():
                            raise
                        torch.cuda.empty_cache()
                        print(f"{key} OOM", flush=True)
                        with open(out, "a") as f:  # record the failure: it is a result for the memory claims
                            f.write(json.dumps(dict(config=name, scene=seq.parent.name, seq=seq.name, frames=n,
                                                    n_used=len(images), lowmem=lowmem, oom=True)) + "\n")
                        continue
                    if name == "B1":
                        refs[(seq.parent.name, seq.name, n)] = pred
                    if key in done:
                        continue
                    m = evaluate(pred, gt_depth, gt_c2w, K)
                    if save_poses:
                        (out.parent / "poses").mkdir(exist_ok=True)
                        np.save(out.parent / "poses" / f"{name}__{seq.parent.name}__{seq.name}__{n}.npy",
                                np.asarray(pred["w2c"], dtype=np.float32))
                    if (seq.parent.name, seq.name, n) in refs and name != "B1":
                        m.update(fidelity(pred, refs[(seq.parent.name, seq.name, n)]))
                    row = dict(config=name, scene=seq.parent.name, seq=seq.name, frames=n, r=kw["r"],
                               n_used=len(images), lowmem=lowmem,
                               **{k: float(v) for k, v in m.items()})
                    with open(out, "a") as f:
                        f.write(json.dumps(row) + "\n")
                    print(f"{name:15s} {seq.parent.name:10s} N={n:3d} r={kw['r']} t={m['time']:.1f}s "
                          f"mem={m['peak_gb']:.2f} AUC30={m['auc30']:.1f} ATE={m['ate']:.3f} "
                          f"absrel={m['absrel']:.3f} CD={m['chamfer']:.3f}", flush=True)
        del model
        gc.collect()  # the patched methods form reference cycles; free the weights before loading the next model
        torch.cuda.empty_cache()
    return out
