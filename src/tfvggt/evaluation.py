"""Evaluation on 7-Scenes-layout sequences (7-Scenes, converted TUM RGB-D): camera pose (AUC@30, ATE), depth (AbsRel, delta<1.25) and point cloud (Acc/Comp/Chamfer).

Every metric is scale-invariant (Sim3 / median alignment) because VGGT predicts geometry up to scale.
"""
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from scipy.spatial import cKDTree

from tfvggt import _flash

_flash.ensure()
from flashvggt.utils.load_fn import load_and_preprocess_images  # noqa: E402
from flashvggt.utils.pose_enc import pose_encoding_to_extri_intri

FX = FY = 585.0  # 7-Scenes depth intrinsics (640x480)
CX, CY = 320.0, 240.0


def load_sequence(seq_dir, num_frames):
    seq_dir = Path(seq_dir)
    poses = sorted(seq_dir.glob("*.pose.txt"))
    ids = np.unique(np.linspace(0, len(poses) - 1, num_frames).round().astype(int))
    stems = [poses[i].name.replace(".pose.txt", "") for i in ids]
    images = load_and_preprocess_images([str(seq_dir / f"{s}.color.png") for s in stems])  # [S,3,392,518]
    H, W = images.shape[-2:]
    depths, c2w = [], []
    for s in stems:
        d = Image.open(seq_dir / f"{s}.depth.png").resize((W, H), Image.NEAREST)
        d = np.asarray(d, dtype=np.float32)
        d[(d == 65535) | (d == 0)] = 0
        depths.append(d / 1000.0)
        c2w.append(np.loadtxt(seq_dir / f"{s}.pose.txt"))
    fx, fy, cx, cy = FX, FY, CX, CY
    if (seq_dir / "intrinsics.txt").exists():  # other datasets converted to this layout (scripts/download_tum.py)
        fx, fy, cx, cy = map(float, (seq_dir / "intrinsics.txt").read_text().split())
    K = np.array([[fx * W / 640, 0, cx * W / 640], [0, fy * H / 480, cy * H / 480], [0, 0, 1]])
    return images, np.stack(depths), np.stack(c2w), K


def umeyama(src, dst):
    """Sim3 (s, R, t) minimizing ||s R src + t - dst||."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    xs, xd = src - mu_s, dst - mu_d
    cov = xd.T @ xs / len(src)
    U, D, Vt = np.linalg.svd(cov)
    E = np.eye(3)
    if np.linalg.det(U @ Vt) < 0:
        E[2, 2] = -1
    R = U @ E @ Vt
    s = np.trace(np.diag(D) @ E) / xs.var(0).sum()
    return s, R, mu_d - s * R @ mu_s


def _rot_angle(R):
    return np.degrees(np.arccos(np.clip((np.trace(R, axis1=-2, axis2=-1) - 1) / 2, -1, 1)))


def pose_metrics(pred_w2c, gt_c2w):
    gt_w2c = np.linalg.inv(gt_c2w)
    S = len(gt_w2c)
    i, j = np.triu_indices(S, 1)

    def rel(w2c):  # relative pose from i to j
        return w2c[j] @ np.linalg.inv(w2c[i])

    rp, rg = rel(pred_w2c), rel(gt_w2c)
    r_err = _rot_angle(rp[:, :3, :3] @ np.transpose(rg[:, :3, :3], (0, 2, 1)))
    tp, tg = rp[:, :3, 3], rg[:, :3, 3]
    cos = (tp * tg).sum(1) / (np.linalg.norm(tp, axis=1) * np.linalg.norm(tg, axis=1) + 1e-9)
    t_err = np.degrees(np.arccos(np.clip(np.abs(cos), -1, 1)))
    err = np.maximum(r_err, t_err)
    auc30 = np.mean([(err < th).mean() for th in range(1, 31)]) * 100
    # ATE on camera centres after Sim3 alignment
    cp = np.linalg.inv(pred_w2c)[:, :3, 3]
    cg = gt_c2w[:, :3, 3]
    s, R, t = umeyama(cp, cg)
    ate = np.sqrt((((s * cp @ R.T + t) - cg) ** 2).sum(1).mean())
    return dict(auc30=auc30, rra=r_err.mean(), rta=t_err.mean(), ate=ate)


def depth_metrics(pred, gt):
    m = gt > 0
    p, g = pred[m], gt[m]
    p = p * np.median(g) / np.median(p)
    ratio = np.maximum(p / g, g / p)
    return dict(absrel=np.mean(np.abs(p - g) / g), d125=(ratio < 1.25).mean() * 100)


def backproject(depth, K, c2w):
    """depth [S,H,W] -> world points [S,H,W,3]."""
    S, H, W = depth.shape
    u, v = np.meshgrid(np.arange(W), np.arange(H))
    x = (u - K[0, 2]) / K[0, 0]
    y = (v - K[1, 2]) / K[1, 1]
    cam = np.stack([x, y, np.ones_like(x)], -1)[None] * depth[..., None]
    return np.einsum("sij,shwj->shwi", c2w[:, :3, :3], cam) + c2w[:, None, None, :3, 3]


def point_metrics(pred_pts, conf, gt_depth, K, gt_c2w, n_samples=200_000, seed=0):
    gt_pts = backproject(gt_depth, K, gt_c2w)
    valid = gt_depth > 0
    valid &= conf >= np.quantile(conf[valid], 0.25)  # drop the least-confident 25% predictions, same rule for all
    p, g = pred_pts[valid], gt_pts[valid]
    rng = np.random.default_rng(seed)
    sel = rng.choice(len(p), min(len(p), n_samples), replace=False)
    s, R, t = umeyama(p[sel], g[sel])
    p = s * p @ R.T + t
    all_g = gt_pts[gt_depth > 0]
    g_s = all_g[rng.choice(len(all_g), min(len(all_g), n_samples), replace=False)]
    p_s = p[rng.choice(len(p), min(len(p), n_samples), replace=False)]
    acc = cKDTree(g_s).query(p_s, workers=-1)[0]
    comp = cKDTree(p_s).query(g_s, workers=-1)[0]
    return dict(acc=acc.mean(), comp=comp.mean(), chamfer=(acc.mean() + comp.mean()) / 2)


@torch.no_grad()
def predict(model, images, device="cuda"):
    lowmem = getattr(model, "lowmem", False)
    if lowmem:  # the streaming forward covers full attention and the grid path; other configs use the standard forward
        lowmem = all(blk.attn.tf.get("sub") or blk.attn.tf["r"] == 1 for blk in model.aggregator.global_blocks)
    if not lowmem:
        images = images.to(device)
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    import time
    t0 = time.time()
    if lowmem:  # streaming forward for long sequences (tfvggt.longseq): CPU images in, CPU outputs
        from tfvggt.longseq import lowmem_forward
        p = lowmem_forward(model, images)
    else:
        with torch.amp.autocast("cuda", dtype=model.amp_dtype):
            p = model(images)
    torch.cuda.synchronize()
    elapsed = time.time() - t0
    extr, _ = pose_encoding_to_extri_intri(p["pose_enc"], images.shape[-2:])
    w2c = np.tile(np.eye(4), (extr.shape[1], 1, 1))
    w2c[:, :3] = extr[0].float().cpu().numpy()
    out = dict(w2c=w2c, depth=p["depth"][0, ..., 0].float().cpu().numpy(),
               conf=p["depth_conf"][0].float().cpu().numpy(),
               points=p["world_points"][0].float().cpu().numpy(),
               time=elapsed, peak_gb=torch.cuda.max_memory_allocated() / 1024**3)
    del p, images
    torch.cuda.empty_cache()
    return out


def evaluate(pred, gt_depth, gt_c2w, K):
    m = dict(time=pred["time"], peak_gb=pred["peak_gb"])
    m.update(pose_metrics(pred["w2c"], gt_c2w))
    m.update(depth_metrics(pred["depth"], gt_depth))
    m.update(point_metrics(pred["points"], pred["conf"], gt_depth, K, gt_c2w))
    return m


def fidelity(pred, ref):
    """How far a configuration drifts from the full-attention reference output (no ground truth involved)."""
    d = pred["depth"] * np.median(ref["depth"]) / np.median(pred["depth"])
    return dict(fid_depth=np.mean(np.abs(d - ref["depth"]) / ref["depth"]),
                fid_pose=pose_metrics(pred["w2c"], np.linalg.inv(ref["w2c"]))["auc30"])
