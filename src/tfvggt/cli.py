"""Command line: `tfvggt <command>` (or `python -m tfvggt <command>`). Same commands on Kaggle and locally.

    tfvggt run --dataset tum:fr3_sitting_xyz --frames 100 200 --configs B1 AVU-c40
    tfvggt run --data data/7scenes --scenes office chess --frames 50 --configs all
    tfvggt download --dataset 7scenes:office/seq-06 tum:fr1_xyz
    tfvggt configs
    tfvggt summary results/run.jsonl
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def _add_run(sub):
    p = sub.add_parser("run", help="evaluate configurations on sequences (one JSON line per config, sequence, N)")
    p.add_argument("--dataset", nargs="*", default=[], metavar="SPEC",
                   help="tum:<name> | 7scenes:<scene>[/<seq>]; downloaded when missing")
    p.add_argument("--data", help="folder of prepared sequences laid out as <scene>/<seq>/ (instead of / besides --dataset)")
    p.add_argument("--scenes", nargs="*", help="with --data: only these scene folders")
    p.add_argument("--frames", type=int, nargs="+", default=[100], help="numbers of frames N (sampled evenly)")
    p.add_argument("--configs", nargs="+", default=["recommended"],
                   help="config names, 'recommended' (default) or 'all'; see `tfvggt configs`")
    p.add_argument("--tag", default="run", help="output file name: <out>/<tag>.jsonl")
    p.add_argument("--out", help="results folder (default: ./results, or /kaggle/working/results on Kaggle)")
    p.add_argument("--lowmem", action="store_true",
                   help="streaming low-memory forward; needed for N >= ~250 on a 16 GB GPU, same results")
    p.add_argument("--save-poses", action="store_true", help="also save predicted world-to-camera poses (.npy)")
    p.add_argument("--plan", nargs="*", default=[], metavar="CFG:N,N",
                   help="per-config frame counts, e.g. B1:400 AVE-s4e36:400,800")
    p.add_argument("--progress", action=argparse.BooleanOptionalAction, default=None,
                   help="per-layer progress lines in low-memory mode (default: on when running on Kaggle)")


def _configs(names):
    from tfvggt.configs import CONFIGS, RECOMMENDED
    out = []
    for n in names:
        out += RECOMMENDED if n == "recommended" else list(CONFIGS) if n == "all" else [n]
    return list(dict.fromkeys(out))


def cmd_run(a):
    from tfvggt import paths
    if a.progress or (a.progress is None and paths.on_kaggle()):
        os.environ["TFVGGT_PROGRESS"] = "1"  # read when tfvggt.longseq is imported
    from tfvggt.datasets import resolve, sequences_in
    if not a.dataset and not a.data:
        sys.exit("give sequences with --dataset SPEC ... and/or --data FOLDER")
    seqs = [resolve(s) for s in a.dataset]
    if a.data:
        found = sequences_in(a.data, a.scenes)
        if not found:
            sys.exit(f"no prepared sequence (<scene>/<seq>/done) under {a.data}")
        seqs += found
    plan = {c: {int(x) for x in ns.split(",")} for c, ns in (t.split(":") for t in a.plan)}
    configs = _configs(a.configs)
    configs += [c for c in plan if c not in configs]
    out = Path(a.out) if a.out else paths.out_dir()
    print(f"[tfvggt] {len(seqs)} sequence(s), N={a.frames}, configs={configs}, lowmem={a.lowmem}, "
          f"results -> {out / (a.tag + '.jsonl')}", flush=True)
    from tfvggt.runner import run
    run(seqs, a.frames, configs, out / f"{a.tag}.jsonl", lowmem=a.lowmem, save_poses=a.save_poses, plan=plan)


def cmd_download(a):
    from tfvggt.datasets import resolve
    for s in a.dataset:
        print(resolve(s), flush=True)


def cmd_configs(a):
    from tfvggt.configs import CONFIGS, RECOMMENDED
    for name in RECOMMENDED + [c for c in CONFIGS if c not in RECOMMENDED]:
        w, kw = CONFIGS[name]
        mark = "*" if name in RECOMMENDED else " "
        print(f"{mark} {name:22s} {w:5s} {kw}")
    print("\n* = recommended (README: 'Chọn cấu hình')")


def cmd_summary(a):
    """Mean of the main metrics per (N, config) over every sequence in the given result files."""
    rows = [json.loads(ln) for f in a.files for ln in Path(f).read_text().splitlines() if ln.strip()]
    rows = [r for r in rows if not r.get("oom")]
    agg = defaultdict(list)
    for r in rows:
        agg[(r["frames"], r["config"])].append(r)
    cols = ["auc30", "ate", "absrel", "chamfer", "time", "peak_gb"]
    print("| N | config | sequences | " + " | ".join(cols) + " |")
    print("|---|---|---|" + "---|" * len(cols))
    for (n, c), rs in sorted(agg.items()):
        vals = " | ".join(f"{sum(r[k] for r in rs) / len(rs):.3f}" for k in cols)
        print(f"| {n} | {c} | {len(rs)} | {vals} |")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="tfvggt", description="Training-free faster VGGT inference.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    _add_run(sub)
    d = sub.add_parser("download", help="download / prepare sequences without running anything")
    d.add_argument("--dataset", nargs="+", required=True, metavar="SPEC")
    sub.add_parser("configs", help="list the named configurations")
    s = sub.add_parser("summary", help="mean metrics per (N, config) of result files")
    s.add_argument("files", nargs="+")
    a = ap.parse_args(argv)
    {"run": cmd_run, "download": cmd_download, "configs": cmd_configs, "summary": cmd_summary}[a.cmd](a)


if __name__ == "__main__":
    main()
