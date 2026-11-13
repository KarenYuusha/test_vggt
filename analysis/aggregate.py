"""Pool every run over the three disjoint sets of 7-Scenes sequences (20 sequences) and print markdown tables.

    python analysis/aggregate.py
Set A = first test sequence of each scene, set B = held-out, set C = set 2. Each (set, scene) is one sequence.
"""
import json
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "results"
SOURCES = {
    "A": ["kaggle/short/short.jsonl", "kaggle/n100/n100.jsonl", "kaggle/n200/n200.jsonl", "kaggle/kf-test/kf-test.jsonl"],
    "B": ["kaggle/ho-short/ho-short.jsonl", "kaggle/ho-long/ho-long.jsonl", "kaggle/kf-heldout/kf-heldout.jsonl"],
    "C": ["s2-local.jsonl", "kaggle/s2-n200-*/s2-n200.jsonl", "kaggle/s2-ref-*/s2-ref.jsonl"],
}
CONFIGS = ["B1", "E1-all", "E1-all-r2", "E2-all", "E2-all-r2", "K-r2k10", "K-r3k10", "Ref-flash"]
T4_TIME_SOURCES = {"kaggle"}  # timing only from Kaggle T4 runs (the local GPU was shared)


def load():
    d = defaultdict(dict)  # (set, scene, N) -> config -> row (first occurrence wins, B1 duplicates agree to ~0.3)
    for s, pats in SOURCES.items():
        for pat in pats:
            for f in sorted(R.glob(pat)):
                for line in open(f):
                    if not line.strip():
                        continue
                    r = json.loads(line)
                    r["_t4"] = f.relative_to(R).parts[0] in T4_TIME_SOURCES
                    d[(s, r["scene"], r["frames"])].setdefault(r["config"], r)
    return d


def main():
    d = load()
    for n in (25, 50, 100, 200):
        keys = [k for k in d if k[2] == n]
        print(f"\n### N = {n}\n")
        print("| config | seq | AUC@30 | Δ vs B1 (same seq) | worst Δ | seq within 2 of B1 | Chamfer | fid_pose | T4 time |")
        print("|---|---|---|---|---|---|---|---|---|")
        for c in CONFIGS:
            ks = [k for k in keys if c in d[k] and "B1" in d[k]]
            if not ks:
                continue
            auc = sum(d[k][c]["auc30"] for k in ks) / len(ks)
            delta = [d[k][c]["auc30"] - d[k]["B1"]["auc30"] for k in ks]
            cd = sum(d[k][c]["chamfer"] for k in ks) / len(ks)
            fids = [d[k][c]["fid_pose"] for k in ks if "fid_pose" in d[k][c]]
            ts = [d[k][c]["time"] for k in ks if d[k][c]["_t4"]]
            print(f"| {c} | {len(ks)} | {auc:.1f} | {sum(delta) / len(ks):+.1f} | {min(delta):+.1f} | "
                  f"{sum(x >= -2 for x in delta)}/{len(ks)} | {cd:.3f} | "
                  f"{sum(fids) / len(fids) if fids else float('nan'):.1f} | "
                  f"{sum(ts) / len(ts) if ts else float('nan'):.0f} s ({len(ts)}) |")


if __name__ == "__main__":
    main()
