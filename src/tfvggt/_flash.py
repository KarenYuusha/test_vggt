"""Make the FlashVGGT code base importable (model definition and utilities; it is used read-only, never modified).

Order:
  1. an installed / importable `flashvggt` (e.g. `pip install -e <flashvggt repo>`),
  2. the repository at $FLASHVGGT_ROOT,
  3. a pinned shallow clone in the cache directory (made once, then reused).
The pinned commit is the one every result in results/ was produced with.
"""
import importlib
import os
import subprocess
import sys
from pathlib import Path

REPO = "https://github.com/wzpscott/flashvggt.git"
COMMIT = "93efde68bf5c7ba2ad9ef41c5b2314c27aff7f25"
_PROBE = "flashvggt.models.flash_vggt"


def _importable():
    try:
        importlib.import_module(_PROBE)
        return True
    except ModuleNotFoundError as e:
        if e.name and (e.name == "flashvggt" or e.name.startswith("flashvggt.")):
            return False
        raise  # flashvggt was found but one of its own dependencies is missing: report that, do not hide it


def _add(root):
    root = str(Path(root).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    for name in [m for m in sys.modules if m == "flashvggt" or m.startswith("flashvggt.")]:
        del sys.modules[name]  # a failed namespace import may have cached an empty package
    importlib.invalidate_caches()


def _clone(dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".partial")
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"[tfvggt] fetching FlashVGGT {COMMIT[:7]} into {dest}", flush=True)
    for cmd in (["git", "init", "-q", str(tmp)],
                ["git", "-C", str(tmp), "fetch", "-q", "--depth", "1", REPO, COMMIT],
                ["git", "-C", str(tmp), "checkout", "-q", "FETCH_HEAD"]):
        subprocess.run(cmd, check=True)
    tmp.rename(dest)


def ensure():
    """Import-time hook used by the modules that need flashvggt. Returns the FlashVGGT repository root."""
    if _importable():
        return root()
    env = os.environ.get("FLASHVGGT_ROOT")
    if env:
        _add(env)
        if _importable():
            return root()
        raise ImportError(f"FLASHVGGT_ROOT={env} does not contain the flashvggt package")
    from tfvggt.paths import cache_dir
    dest = cache_dir() / f"flashvggt-{COMMIT[:7]}"
    if not (dest / "flashvggt").is_dir():
        _clone(dest)
    _add(dest)
    if not _importable():
        raise ImportError(f"could not import flashvggt from {dest}")
    return root()


def root():
    """Root of the FlashVGGT repository in use (its ckpts/ folder is searched for checkpoints)."""
    import flashvggt
    return Path(next(iter(flashvggt.__path__))).resolve().parent
