"""Average every metric over scenes for each (frames, config). Usage: python analysis/summarize.py results/kaggle/*/*.jsonl"""
import json
import sys
from collections import defaultdict

COLS = ["time", "peak_gb", "auc30", "ate", "absrel", "d125", "acc", "comp", "chamfer", "fid_depth", "fid_pose"]
ORDER = ["B1", "E1-flash", "E1-all", "E2-all", "E2-a05", "E2-avg", "E3-budget", "E2-flash", "E1-all-r2", "E2-all-r2",
         "E1-all-r4", "E2-all-r4", "K-r2k10", "K-r3k10", "Ref-flash", "Ref-flash-mass"]


def main(paths):
    rows = [json.loads(line) for p in paths for line in open(p) if line.strip()]
    groups = defaultdict(list)
    for r in rows:
        groups[(r["frames"], r["config"])].append(r)
    for n in sorted({k[0] for k in groups}):
        print(f"\n### N = {n} frames (mean over scenes)\n")
        print("| config | scenes | r | " + " | ".join(COLS) + " |")
        print("|" + "---|" * (len(COLS) + 3))
        base_t = None
        for c in ORDER:
            g = groups.get((n, c))
            if not g:
                continue
            mean = {k: sum(r.get(k, float("nan")) for r in g) / len(g) for k in COLS}
            if c == "B1":
                base_t = mean["time"]
            rs = sorted({str(r["r"]) for r in g})
            cells = [f"{mean[k]:.3f}" if k not in ("auc30", "d125", "fid_pose") else f"{mean[k]:.1f}" for k in COLS]
            if base_t and c != "B1":
                cells[0] += f" ({base_t / mean['time']:.1f}x)"
            print(f"| {c} | {len(g)} | {','.join(rs)} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main(sys.argv[1:])
