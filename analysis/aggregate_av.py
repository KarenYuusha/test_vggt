"""AVGGT comparison: pool the av-* Kaggle runs (+ earlier K-r2k10 / Ref-flash T4 rows) over the 20 sequences.

    python analysis/aggregate_av.py
Validation = the 18 sequences not used to pick the configurations; the 2 development sequences (office seq-06,
chess seq-05) are reported separately. Every number is from Kaggle T4 (fp16).
"""
import json
from collections import defaultdict
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "results" / "kaggle"
DEV = {("office", "seq-06"), ("chess", "seq-05")}
SOURCES = ["av-*/*.jsonl", "kf-test/*.jsonl", "kf-heldout/*.jsonl", "s2-n200-*/*.jsonl", "s2-ref-*/*.jsonl",
           "n100/*.jsonl", "n200/*.jsonl", "short/*.jsonl", "ho-short/*.jsonl", "ho-long/*.jsonl"]
CONFIGS = ["B1", "AV-s4", "AV-s9", "AVE-s4e36", "AVEK-s9e36k10", "K-r2k10", "Ref-flash"]
# sequence of the rows written before the seq field existed (one sequence per scene in those runs)
LEGACY_SEQ = {"short": "A", "n100": "A", "n200": "A", "ho-short": "B", "ho-long": "B"}
SETS = {"A": {"chess": "seq-03", "fire": "seq-03", "heads": "seq-01", "office": "seq-02", "pumpkin": "seq-01",
              "redkitchen": "seq-03", "stairs": "seq-01"},
        "B": {"chess": "seq-05", "fire": "seq-04", "heads": "seq-02", "office": "seq-06", "pumpkin": "seq-07",
              "redkitchen": "seq-04", "stairs": "seq-04"}}


def load():
    d = defaultdict(dict)  # (scene, seq, N) -> config -> row; av-* runs first so their B1 is the reference
    for pat in SOURCES:
        for f in sorted(R.glob(pat)):
            run = f.parent.name
            for line in open(f):
                if not line.strip():
                    continue
                r = json.loads(line)
                seq = r.get("seq") or SETS[LEGACY_SEQ[run]][r["scene"]]
                d[(r["scene"], seq, r["frames"])].setdefault(r["config"], r)
    return d


def table(d, keys, title):
    print(f"\n#### {title}\n")
    print("| config | seq | AUC@30 | Δ vs B1 | worst Δ | within 2 | Chamfer | fid_pose | T4 time | speed-up | peak GB |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in CONFIGS:
        ks = [k for k in keys if c in d[k] and "B1" in d[k]]
        if not ks:
            continue
        auc = sum(d[k][c]["auc30"] for k in ks) / len(ks)
        delta = [d[k][c]["auc30"] - d[k]["B1"]["auc30"] for k in ks]
        cd = sum(d[k][c]["chamfer"] for k in ks) / len(ks)
        fids = [d[k][c]["fid_pose"] for k in ks if "fid_pose" in d[k][c]]
        t = sum(d[k][c]["time"] for k in ks) / len(ks)
        tb = sum(d[k]["B1"]["time"] for k in ks) / len(ks)
        mem = max(d[k][c].get("peak_gb", float("nan")) for k in ks)
        print(f"| {c} | {len(ks)} | {auc:.1f} | {sum(delta) / len(ks):+.1f} | {min(delta):+.1f} | "
              f"{sum(x >= -2 for x in delta)}/{len(ks)} | {cd:.3f} | "
              f"{sum(fids) / len(fids) if fids else float('nan'):.1f} | {t:.0f} s | {tb / t:.1f}× | {mem:.2f} |")


def main():
    d = load()
    for n in (50, 100, 200):
        keys = [k for k in d if k[2] == n and "AV-s4" in d[k]]
        table(d, [k for k in keys if k[:2] not in DEV], f"N = {n}, validation ({len([k for k in keys if k[:2] not in DEV])} sequences)")
        table(d, [k for k in keys if k[:2] in DEV], f"N = {n}, development (office seq-06, chess seq-05)")


if __name__ == "__main__":
    main()
