"""Low-memory forward for long sequences (training-free, same arithmetic per token as the standard forward).

The standard forward keeps, for N frames of P tokens:
  - the four DPT intermediate layers on the GPU ([N, P, 2C] each),
  - block-wide temporaries (LayerNorm output, q/k/v, attention output, residuals) for all N*P tokens at once,
  - all head outputs on the GPU.
With attention compressed, none of this shrinks, so a 16 GB T4 stops at about N=250 whatever the attention scheme.

Here:
  - frame blocks run on small groups of frames,
  - a global block runs in two streaming passes over token chunks: pass 1 projects keys/values and keeps only the
    compressed key set (grid patches + whole frames + camera/register tokens) plus the mean-fill sums; pass 2
    projects the queries of a chunk, attends to the kept keys (+ diagonal, mean), and applies the residual, the MLP and
    its residual to that chunk in place. Keys are taken from the block input, exactly as in the standard block,
  - DPT intermediates are moved to CPU memory as they are produced; the heads read them back frame chunk by frame chunk,
  - predictions are returned on the CPU.
Supported attention configs: full attention (B1) and the grid path of tfvggt.core (sub, early_sub, diag, mean,
keyframes, shift, wsel). Not supported: the older nearest-pool path, the neighbour pass, query reduction.
"""
import os
import time

import torch

from tfvggt import _flash

_flash.ensure()
from flashvggt.models import aggregator as agg_mod  # noqa: E402
from flashvggt.utils.geometry_cuda import unproject_depth_map_to_point_map
from flashvggt.utils.pose_enc import pose_encoding_to_extri_intri

from tfvggt.core import _attn_lse, _autocast_dtype, _prefix_mass, _window_mask


_PROGRESS = os.environ.get("TFVGGT_PROGRESS") == "1"


def _proj(attn, h, pos):
    """q, k, v [1, H, n, D] for a token chunk h [1, n, C] (same ops as the attention module)."""
    n = h.shape[1]
    qkv = attn.qkv(h).reshape(1, n, 3, attn.num_heads, attn.head_dim).permute(2, 0, 3, 1, 4)
    q, k, v = qkv.unbind(0)
    q, k = attn.q_norm(q), attn.k_norm(k)
    if attn.rope is not None:
        q, k = attn.rope(q, pos), attn.rope(k, pos)
    dt = _autocast_dtype() if torch.is_autocast_enabled() else v.dtype
    return (t.to(dt).contiguous() for t in (q, k, v))


def _key_masks(cfg, S, P, P0, pH, pW, kf, device, score=None):
    """keep [S, P]: keys in the compressed set; dropped [S, P]: patch keys left out (for diagonal and mean fill).
    score [S, pH*pW]: content-adaptive grid (wsel), best patch of every window."""
    keep = torch.ones(S, P, dtype=torch.bool, device=device)
    if not cfg.get("sub"):
        return keep, ~keep
    sh, sw = cfg["sub"]
    if score is not None:
        keep[:, P0:] = _window_mask(score, pH, pW, sh, sw)
    else:
        for f in range(S):
            ph = f % (sh * sw) if cfg.get("shift") else 0
            g = torch.zeros(pH, pW, dtype=torch.bool, device=device)
            g[ph // sw::sh, ph % sw::sw] = True
            keep[f, P0:] = g.flatten()
    whole = torch.zeros(S, dtype=torch.bool, device=device)
    whole[0] = True
    if kf is not None:
        whole[kf] = True
    keep[whole] = True
    return keep, ~keep


@torch.no_grad()
def _stream_score(blk, x, pos, S, P, P0, chunk, mode):
    """Content-adaptive grid scores [S, pH*pW], streamed (same values as tfvggt.core._key_score)."""
    attn = blk.attn
    N = S * P
    sc = torch.empty(N, dtype=torch.float32, device=x.device)
    if mode == "norm":
        for i in range(0, N, chunk):
            sl = slice(i, i + chunk)
            _, k, _ = _proj(attn, blk.norm1(x[sl][None]), pos[sl][None])
            sc[sl] = k[0].float().norm(dim=-1).sum(0)
        return sc.view(S, P)[:, P0:]
    pidx = (torch.arange(S, device=x.device)[:, None] * P + torch.arange(P0, device=x.device)[None]).flatten()
    qp, _, _ = _proj(attn, blk.norm1(x[pidx][None]), pos[pidx][None])
    lse = None
    for i in range(0, N, chunk):  # log-sum-exp of every camera/register query over all keys, chunk by chunk
        sl = slice(i, i + chunk)
        _, k, v = _proj(attn, blk.norm1(x[sl][None]), pos[sl][None])
        lc = _attn_lse(qp, k, v)[1].float()
        lse = lc if lse is None else torch.logaddexp(lse, lc)
    for i in range(0, N, chunk):
        sl = slice(i, i + chunk)
        _, k, _ = _proj(attn, blk.norm1(x[sl][None]), pos[sl][None])
        sc[sl] = _prefix_mass(qp, k, lse)
    return sc.view(S, P)[:, P0:]


@torch.no_grad()
def _stream_global(blk, x, pos, S, P, P0, pH, pW, kf, chunk):
    """x: [S*P, C] tokens (modified in place), pos: [S*P, 2]."""
    attn, cfg = blk.attn, blk.attn.tf
    assert not cfg.get("nbr") and not cfg.get("qsub"), "streaming supports the grid path without nbr/qsub"
    assert cfg.get("sub") or cfg["r"] == 1, "streaming supports full attention or the grid path"
    N = S * P
    H, D = attn.num_heads, attn.head_dim
    score = _stream_score(blk, x, pos, S, P, P0, chunk, cfg["wsel"]) if cfg.get("wsel") else None
    keep, dropped = _key_masks(cfg, S, P, P0, pH, pW, kf, x.device, score)
    keep, dropped = keep.flatten(), dropped.flatten()
    dst = torch.cumsum(keep, 0) - 1
    nk = int(keep.sum())
    use_mean = cfg.get("sub") and cfg.get("mean") and bool(dropped.any())
    use_diag = cfg.get("sub") and cfg.get("diag") and bool(dropped.any())
    kbuf = vbuf = None
    ksum = vsum = None
    for i in range(0, N, chunk):  # pass 1: compressed keys/values from the block input
        sl = slice(i, i + chunk)
        _, k, v = _proj(attn, blk.norm1(x[sl][None]), pos[sl][None])
        if kbuf is None:
            kbuf = torch.empty(1, H, nk, D, dtype=k.dtype, device=x.device)
            vbuf = torch.empty_like(kbuf)
            ksum = torch.zeros(H, D, dtype=torch.float32, device=x.device)
            vsum = torch.zeros_like(ksum)
        m = keep[sl]
        kbuf[:, :, dst[sl][m]] = k[:, :, m]
        vbuf[:, :, dst[sl][m]] = v[:, :, m]
        if use_mean:
            dm = dropped[sl]
            ksum += k[0][:, dm].float().sum(1)
            vsum += v[0][:, dm].float().sum(1)
    scale = D ** -0.5
    if use_mean:
        cnt = float(dropped.sum())
        km, vm = (ksum / cnt).to(kbuf.dtype), (vsum / cnt).to(vbuf.dtype)
    # pass 2 reads every chunk's input before writing it, and keys come from pass 1, so updating x in place is exact
    beat = time.time()
    for i in range(0, N, chunk):
        sl = slice(i, i + chunk)
        if _PROGRESS and time.time() - beat > 60:  # heartbeat: a full-attention layer at N=800 takes ~5 min
            torch.cuda.synchronize()
            print(f"[lowmem]   chunk {i // chunk}/{(N + chunk - 1) // chunk}", flush=True)
            beat = time.time()
        xc = x[sl][None]
        q, k, v = _proj(attn, blk.norm1(xc), pos[sl][None])
        o, lse = _attn_lse(q, kbuf, vbuf)
        terms = [(o, lse)]
        if use_mean:
            terms.append((vm[None, :, None], (q[0] @ km[:, :, None]).squeeze(-1).float()[None] * scale))
        if use_diag:
            s = (q * k).sum(-1, dtype=torch.float32) * scale
            terms.append((v, s.masked_fill(~dropped[sl], -float("inf"))))
        if len(terms) > 1:
            w = torch.softmax(torch.stack([l for _, l in terms]), 0).to(o.dtype)[..., None]
            o = sum(t * wt for (t, _), wt in zip(terms, w))
        o = attn.proj_drop(attn.proj(o.transpose(1, 2).reshape(1, -1, H * D)))
        xc = xc + blk.ls1(o)
        xc = xc + blk.ls2(blk.mlp(blk.norm2(xc)))
        x[sl] = xc[0]
    return x


@torch.no_grad()
def _frame_groups(blk, tokens, pos, group):
    """tokens: [S, P, C] (in place), run a frame-attention block on `group` frames at a time."""
    for i in range(0, tokens.shape[0], group):
        tokens[i:i + group] = blk(tokens[i:i + group], pos=pos[i:i + group])


@torch.no_grad()
def lowmem_forward(model, images, frame_group=16, chunk=16384, dpt_chunk=2, offload=True, img_chunk=8,
                   device="cuda"):
    """images [S, 3, H, W] (CPU or GPU) -> dict of CPU tensors (pose_enc, depth, depth_conf, world_points).
    Images are moved to the GPU a chunk at a time; patch tokens are written straight into one token buffer."""
    agg = model.aggregator
    images = images[None]
    B, S, _, Hh, Ww = images.shape
    pH, pW = Hh // agg.patch_size, Ww // agg.patch_size
    P0 = agg.patch_start_idx
    P = P0 + pH * pW
    with torch.amp.autocast("cuda", dtype=model.amp_dtype):
        tokens = None
        for i in range(0, S, img_chunk):
            x = (images[0, i:i + img_chunk].to(device) - agg._resnet_mean[0]) / agg._resnet_std[0]
            patch = agg.patch_embed(x)
            if isinstance(patch, dict):
                patch = patch["x_norm_patchtokens"]
            if tokens is None:
                tokens = torch.empty(S, P, patch.shape[-1], dtype=patch.dtype, device=device)
            tokens[i:i + img_chunk, P0:] = patch
            del x, patch
        cam = agg_mod.slice_expand_and_flatten(agg.camera_token, B, S)
        reg = agg_mod.slice_expand_and_flatten(agg.register_token, B, S)
        tokens[:, :P0] = torch.cat([cam, reg], dim=1).to(tokens.dtype)
        del cam, reg
        pos = agg.position_getter(S, pH, pW, device=device)
        if P0 > 0:
            pos = torch.cat([torch.zeros(S, P0, 2, device=device, dtype=pos.dtype), pos + 1], dim=1)
        C = tokens.shape[-1]
        kfi = agg_mod.select_keyframes(tokens, B, S, P, C, agg.keyframe_every)
        kf = kfi[0].unique()
        dtype = model.amp_dtype
        keep_idx = set(model.depth_head.intermediate_layer_idx) | {agg.depth - 1}
        outs = [None] * agg.depth
        progress = os.environ.get("TFVGGT_PROGRESS") == "1"  # one line per layer, so a stalled run is visible
        t0 = time.time()
        for i in range(agg.depth):
            if progress:
                torch.cuda.synchronize()
                print(f"[lowmem] S={S} layer {i}/{agg.depth} {time.time() - t0:.0f}s", flush=True)
            _frame_groups(agg.frame_blocks[i], tokens, pos, frame_group)
            f_out = tokens.to(dtype).to("cpu" if offload else tokens.device, copy=True) if i in keep_idx else None
            if agg.global_start_idx <= i <= agg.global_end_idx:
                _stream_global(agg.global_blocks[i], tokens.view(S * P, C), pos.view(S * P, 2), S, P, P0, pH, pW,
                               kf, chunk)
            else:
                _frame_groups(agg.global_blocks[i], tokens, pos, frame_group)
            if i in keep_idx:
                g_out = tokens.to(dtype).to(f_out.device, copy=True)
                outs[i] = torch.cat([f_out, g_out], dim=-1)[None]  # [1, S, P, 2C]
                del f_out, g_out
        del tokens

    pred = {}
    with torch.amp.autocast("cuda", enabled=False):
        last = outs[-1][:, :, :1].to(device)  # the camera head reads the camera token of the last layer only
        pose_enc = model.camera_head([last])[-1]
        pred["pose_enc"] = pose_enc.cpu()
        extr, intr = pose_encoding_to_extri_intri(pose_enc, images.shape[-2:])
        depth, conf, pts = [], [], []
        for s in range(0, S, dpt_chunk):
            e = min(s + dpt_chunk, S)
            lst = [t[:, s:e].to(device) if t is not None else None for t in outs]
            d, c = model.depth_head._forward_impl(lst, images[:, s:e].to(device), P0)
            p = unproject_depth_map_to_point_map(d.flatten(0, 1), extr[0, s:e], intr[0, s:e])
            depth.append(d.cpu()), conf.append(c.cpu()), pts.append(p.cpu())
            del lst
        pred["depth"] = torch.cat(depth, 1)
        pred["depth_conf"] = torch.cat(conf, 1)
        pred["world_points"] = torch.cat(pts, 0)[None]
    return pred
