"""Dataset specs -> sequence folders in the 7-Scenes layout (<root>/<scene>/<seq>/ with a `done` marker).

  tum:<name>             a TUM RGB-D sequence, e.g. tum:fr3_sitting_xyz or tum:fr2_pioneer_slam3
  7scenes:<scene>/<seq>  a 7-Scenes sequence, e.g. 7scenes:office/seq-06
  7scenes:<scene>        the scene's first test sequence
A sequence that already exists under an attached read-only input (Kaggle datasets in /kaggle/input) or in the data
folder is used as is; otherwise it is downloaded into the data folder.
"""
from pathlib import Path

from tfvggt.paths import data_dir, input_roots


def _find_prepared(scene, seq):
    for base in input_roots():
        for done in base.glob(f"**/{scene}/{seq}/done"):
            return done.parent
    return None


def resolve(spec, root=None):
    """One dataset spec -> the sequence folder (downloading it if needed)."""
    root = Path(root) if root else data_dir()
    kind, _, name = spec.partition(":")
    if kind == "tum":
        from tfvggt.datasets import tum
        tum.lookup(name)  # validate before searching
        return _find_prepared(name, "seq-01") or tum.download(name, root)
    if kind == "7scenes":
        from tfvggt.datasets import sevenscenes
        scene, _, seq = name.partition("/")
        if seq:
            return _find_prepared(scene, seq) or sevenscenes.download(scene, seq, root)
        return sevenscenes.download(scene, 0, root)
    raise ValueError(f"unknown dataset spec {spec!r}: expected tum:<name> or 7scenes:<scene>[/<seq>]")


def sequences_in(folder, scenes=None):
    """Every prepared sequence under a folder laid out as <folder>/<scene>/<seq>/done."""
    seqs = sorted(p.parent for p in Path(folder).resolve().glob("*/*/done"))
    return [s for s in seqs if not scenes or s.parent.name in scenes]
