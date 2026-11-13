"""Where things live, so the same command runs unchanged on Kaggle and on a local machine.

                 Kaggle                         local
  data           /tmp/tfvggt/data               ./data
  results        /kaggle/working/results        ./results
  cache          /tmp/tfvggt/cache              ~/.cache/tfvggt
Every default can be overridden: TFVGGT_DATA, TFVGGT_OUT, TFVGGT_CACHE, TFVGGT_CKPT_DIR (or the CLI options).
On Kaggle, data and the cache stay out of /kaggle/working so they are not saved as kernel output.
"""
import os
from pathlib import Path

CKPT_FILES = {"vggt": "vggt_1b.pt", "flash": "flashvggt.pt"}
HF_FILES = {"vggt": ("facebook/VGGT-1B", "model.pt"), "flash": ("ZipW/FlashVGGT", "flashvggt.pt")}


def on_kaggle():
    return Path("/kaggle/working").is_dir() or "KAGGLE_KERNEL_RUN_TYPE" in os.environ


def data_dir():
    if os.environ.get("TFVGGT_DATA"):
        return Path(os.environ["TFVGGT_DATA"])
    return Path("/tmp/tfvggt/data") if on_kaggle() else Path.cwd() / "data"


def out_dir():
    if os.environ.get("TFVGGT_OUT"):
        return Path(os.environ["TFVGGT_OUT"])
    return Path("/kaggle/working/results") if on_kaggle() else Path.cwd() / "results"


def cache_dir():
    if os.environ.get("TFVGGT_CACHE"):
        return Path(os.environ["TFVGGT_CACHE"])
    return Path("/tmp/tfvggt/cache") if on_kaggle() else Path.home() / ".cache" / "tfvggt"


def input_roots():
    """Read-only folders searched for already-prepared sequences before downloading (attached Kaggle datasets)."""
    return [Path("/kaggle/input")] if Path("/kaggle/input").is_dir() else []


def checkpoint(weights="vggt"):
    """Path of the checkpoint for `weights` ("vggt" = original VGGT-1B, "flash" = fine-tuned FlashVGGT).
    Looks in $TFVGGT_CKPT_DIR and <FlashVGGT repo>/ckpts first, then downloads from Hugging Face (cached)."""
    name = CKPT_FILES[weights]
    dirs = []
    if os.environ.get("TFVGGT_CKPT_DIR"):
        dirs.append(Path(os.environ["TFVGGT_CKPT_DIR"]))
    from tfvggt import _flash
    dirs.append(_flash.ensure() / "ckpts")
    for d in dirs:
        if (d / name).is_file():
            return d / name
    from huggingface_hub import hf_hub_download
    repo, file = HF_FILES[weights]
    print(f"[tfvggt] downloading {repo}/{file} (first run only)", flush=True)
    return Path(hf_hub_download(repo, file))
