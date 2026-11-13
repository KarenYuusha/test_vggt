"""Peak GPU memory per stage (DINO, aggregator blocks, camera head, depth head) for a given number of frames."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

import torch  # noqa: E402

from tfvggt.core import build_model, configure  # noqa: E402
from tfvggt.evaluation import load_sequence  # noqa: E402

model = build_model("vggt")
from tfvggt.configs import CONFIGS  # noqa: E402
configure(model, **CONFIGS[os.environ.get("MEM_CONFIG", "B1")][1])
agg = model.aggregator
GB = 1024**3
peaks = {}


def stage(mod, name):
    def pre(m, a):
        torch.cuda.synchronize()
        peaks[name + "_start"] = torch.cuda.memory_allocated() / GB
        torch.cuda.reset_peak_memory_stats()

    def post(m, a, o):
        torch.cuda.synchronize()
        peaks[name] = torch.cuda.max_memory_allocated() / GB

    mod.register_forward_pre_hook(pre)
    mod.register_forward_hook(post)


stage(agg.patch_embed, "dino")
stage(agg.frame_blocks[12], "frame_block")
stage(agg.global_blocks[12], "global_block")
stage(model.camera_head, "camera_head")
stage(model.depth_head, "depth_head")
if getattr(model, "point_head", None) is not None:
    stage(model.point_head, "point_head")

seq = sorted((ROOT / "data" / "7scenes" / "chess").glob("seq-*"))[0]
for n in [int(x) for x in sys.argv[1:]] or [25, 50]:
    images = load_sequence(seq, n)[0].to("cuda")
    peaks.clear()
    torch.cuda.reset_peak_memory_stats()
    with torch.no_grad(), torch.amp.autocast("cuda", dtype=model.amp_dtype):
        p = model(images)
    total = torch.cuda.max_memory_allocated() / GB
    print(f"N={n} {os.environ.get('MEM_CONFIG', 'B1')}: " + "  ".join(f"{k}={v:.2f}" for k, v in peaks.items()) + f"  (last peak {total:.2f} GB)")
    del p, images
    torch.cuda.empty_cache()
