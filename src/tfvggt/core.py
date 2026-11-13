"""Training-free efficient VGGT inference on top of the FlashVGGT codebase (imported read-only, never edited).

Two groups of changes, both applied at inference time with frozen weights:

1. Exact memory/time optimizations (output identical up to bf16 rounding):
   - aggregator intermediates kept in bf16 instead of fp32,
   - DPT head run on small frame chunks.
2. Approximate global attention (the research part):
   - per-frame K/V compression (nearest or average pooling) with full-resolution queries,
   - mass correction: each compressed key gets a logit bias alpha * log(#tokens it stands for), so that
     the softmax weight a frame receives matches what it would get with full attention,
   - per-layer compression ratios and an optional token budget that picks r from the number of frames.
"""
import math
import types

import torch
import torch.nn.functional as F

from tfvggt import _flash

_flash.ensure()
from flashvggt.models.flash_vggt import FlashVGGT  # noqa: E402
import flashvggt.models.aggregator as _agg_mod  # noqa: E402

_KEYFRAME_EXTRA = []  # extra keyframes added to the k-means ones (set by configure; diagnostic experiments)
_select_keyframes = _agg_mod.select_keyframes


_KF_UNIF = {"every": 0, "kmeans": True, "count": 0}  # uniform-in-time extra keyframes (set by configure; results/kfx_plan.md)


def uniform_extra(S, m, taken):
    """m frames spread evenly in time (centre of each of m equal segments); a position that is already a keyframe moves
    to the nearest free frame. Deterministic."""
    taken, out = set(taken), []
    for t in range(m):
        p = min(S - 1, int((t + 0.5) * S / m))
        q = next(q for d in range(S) for q in (p + d, p - d) if 0 <= q < S and q not in taken)
        taken.add(q)
        out.append(q)
    return out


def _select_keyframes_extra(tokens, B, S, P, C, keyframe_every=10):
    if _KF_UNIF["kmeans"]:
        idx = _select_keyframes(tokens, B, S, P, C, keyframe_every)
    else:  # no k-means: frame 0 only, plus the uniform extras below
        idx = torch.zeros(B, 1, dtype=torch.long, device=tokens.device)
    extra = [i for i in _KEYFRAME_EXTRA if i < S]
    m = min(_KF_UNIF["count"], S - 1) if _KF_UNIF["count"] else (S // _KF_UNIF["every"] if _KF_UNIF["every"] else 0)
    if m > 0:
        extra += uniform_extra(S, m, set(idx[0].tolist()) | set(extra))
    if extra:
        idx = torch.cat([idx, torch.tensor([extra] * B, dtype=idx.dtype, device=idx.device)], dim=1)
    return idx


_agg_mod.select_keyframes = _select_keyframes_extra

DEPTH = 24
FLASH_RANGE = (9, 19)  # global layers that FlashVGGT keeps cross-frame; the others act as frame attention


class _FloatIn(torch.nn.Module):
    """Runs a head LayerNorm in fp32 on bf16 intermediates."""

    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, x):
        return self.m(x.float())


class _ChunkedMLP(torch.nn.Module):
    """Applies an MLP to at most `chunk` tokens at a time; identical output, far smaller hidden activations."""

    def __init__(self, mlp, chunk):
        super().__init__()
        self.mlp, self.chunk = mlp, chunk

    def forward(self, x):
        flat = x.reshape(-1, x.shape[-1])
        if len(flat) <= self.chunk:
            return self.mlp(x)
        out = torch.cat([self.mlp(flat[i:i + self.chunk]) for i in range(0, len(flat), self.chunk)])
        return out.view(*x.shape[:-1], out.shape[-1])


def build_model(weights="vggt", checkpoint=None, device="cuda", dpt_chunk=2, bf16_inter=True, mlp_chunk=32768,
                dino_chunk=8):
    """weights: "vggt" (original VGGT-1B, used by every training-free config) or "flash" (fine-tuned FlashVGGT).
    checkpoint: explicit path; by default tfvggt.paths.checkpoint finds or downloads it."""
    from tfvggt.paths import checkpoint as find_checkpoint
    model = FlashVGGT(kv_downfactor=1, keyframe_every=10**9)
    sd = torch.load(str(checkpoint or find_checkpoint(weights)), map_location="cpu", mmap=True, weights_only=False)
    for key in ("state_dict", "model"):
        if isinstance(sd, dict) and isinstance(sd.get(key), dict):
            sd = sd[key]
    missing, _ = model.load_state_dict(sd, strict=False)
    assert not missing, f"missing keys: {missing[:5]}"
    del sd

    agg = model.aggregator
    dtype = torch.bfloat16 if torch.cuda.get_device_capability()[0] >= 8 else torch.float16
    agg.to(dtype)
    model.eval().to(device)
    model.amp_dtype = dtype

    # exact optimization 1: bf16 intermediates
    if bf16_inter:
        for name in ("_process_frame_attention", "_process_global_attention", "_process_global_as_frame_attention"):
            fn = getattr(agg, name)

            def wrapped(*a, _fn=fn, **k):
                tokens, idx, inter = _fn(*a, **k)
                return tokens, idx, [t.to(dtype) for t in inter]

            setattr(agg, name, wrapped)
        model.depth_head.norm = _FloatIn(model.depth_head.norm)
        model.camera_head.token_norm = _FloatIn(model.camera_head.token_norm)

    # exact optimization 2: small DPT chunks
    dh_forward = model.depth_head.forward
    model.depth_head.forward = lambda *a, **k: dh_forward(*a, **{**k, "frames_chunk_size": dpt_chunk})

    # exact optimization 3: token-chunked MLPs (the 4096-wide hidden layer is the largest transient in a block)
    if mlp_chunk:
        for blk in list(agg.frame_blocks) + list(agg.global_blocks):
            blk.mlp = _ChunkedMLP(blk.mlp, mlp_chunk)

    # exact optimization 4: DINO patch embedding over small groups of frames
    if dino_chunk:
        pe_forward = agg.patch_embed.forward

        def chunked_patch_embed(images, *a, **k):
            outs = [pe_forward(images[i:i + dino_chunk], *a, **k) for i in range(0, len(images), dino_chunk)]
            if isinstance(outs[0], dict):
                return {key: torch.cat([o[key] for o in outs]) if torch.is_tensor(outs[0][key]) else outs[0][key]
                        for key in outs[0]}
            return torch.cat(outs)

        agg.patch_embed.forward = chunked_patch_embed

    # exact optimization 5 (inside _descriptor_attention): q/k/v built chunk by chunk straight into the half-precision
    # buffers SDPA would cast them to anyway, so the fp32 LayerNorm/RoPE temporaries never exist for all tokens at once
    for blk in list(agg.frame_blocks) + list(agg.global_blocks):
        blk.attn.forward = types.MethodType(_descriptor_attention, blk.attn)
        blk.attn.tf = dict(r=1, pool="nearest", alpha=0.0, dedup=True)
        blk.attn.qkv_chunk = mlp_chunk
    configure(model)
    return model


def configure(model, r=1, layers="all", pool="nearest", alpha=0.0, keyframe_every=None, dedup=True,
              sub=None, diag=False, mean=False, nbr=0, nbr_mode="knn", nbr_self=True, early_sub=None, shift=False,
              qsub=None, qsub_from=0, qsub_keep0=False, qsub_mode="copy", late_sub=None, late_from=17,
              late_frame=False, full_layers=(), band_sub=None, wsel=None, wsel_from=9,
              keyframe_extra=(), keyframe_unif=0, kmeans=True, keyframe_count=0):
    """r: int or list of 24 ints. layers: 'all' (every global layer cross-frame), 'flash' (FlashVGGT layout) or an int
    t (global layers 0..t-1 run as frame attention, as in AVGGT).
    alpha: mass-correction strength (0 = plain compression as in FlashVGGT, 1 = full correction).
    dedup: drop the descriptors of keyframes (already present at full resolution). FlashVGGT keeps them (dedup=False).

    Grid path (used when `sub` is given; r, pool, alpha, keyframes are ignored):
    sub=(sh, sw): keep the first patch of every sh x sw window of every frame except frame 0 (kept whole), plus all
      camera/register tokens; one shared softmax over every part below (merged exactly through log-sum-exp).
    diag: AVGGT diagonal preservation, every query also sees its own key.
    mean: AVGGT mean fill, one extra key/value pair = the mean of all dropped patch keys/values.
    nbr=m: neighbourhood resolution (this work): every frame also sees the dropped patches of m frames (itself and its
      m-1 most similar frames, frame 0 excluded since it is whole), so near views are attended at full resolution and
      far views at grid resolution, with no key counted twice. Generalizes the diagonal (one token -> whole near frames).
    nbr_mode: 'knn' (cosine similarity of the mean patch token of the layer input) or 'temporal' (nearest indices).
    nbr_self: whether a frame's own dropped patches are among its m neighbour frames (False: only other frames).
    early_sub=(sh, sw): with an int `layers`=t, keep global layers 0..t-1 cross-frame on this (coarser) grid instead of
      turning them into frame attention (this work: cheap cross-frame context in the early layers).
    shift: per-frame grid phase (frame f keeps phase f mod sh*sw of every window) instead of one fixed grid (this work).
    qsub=(qh, qw): query-side reduction (this work): global attention is computed only for the camera/register tokens and
      the first patch of every qh x qw window; the other patches reuse their window's attention output (the residual
      update), while the MLP and frame attention still run on every token. Applied to global layers >= qsub_from.
      qsub_keep0: keep every query of the reference frame 0.
      qsub_mode: 'copy' (the whole attention output is shared in the window) or 'lse' (only the shared coarse-key part
      and its log-sum-exp are shared; the diagonal and mean terms are computed for every token and merged exactly).
    late_sub=(sh, sw): coarser grid for global layers >= late_from (the late layers only refine, per AVGGT).
    late_frame: global layers >= late_from run as frame attention instead.
    wsel: content-adaptive grid (this work), for grid layers >= wsel_from: every sh x sw window still keeps one patch
      key, but the one with the highest score instead of the window's first patch. 'pref': attention mass the patch
      receives from the camera/register queries of all frames (exact softmax over all keys); 'norm': key norm.
    full_layers: global layer indices that keep full attention (ablation: which layers does the compression hurt?).
    band_sub=(sh, sw): the full_layers use this finer grid instead of full attention (cheaper band).
    keyframe_extra: frame indices kept whole in addition to the k-means keyframes (results/rotation_plan.md).
    keyframe_unif=u: also keep S//u frames spread evenly in time whole (uniform_extra; results/kfx_plan.md).
    keyframe_count=m: like keyframe_unif but a fixed m frames whatever S (results/longkf_plan.md); overrides keyframe_unif.
    kmeans=False: skip the k-means keyframes (frame 0 and the extras only).
    keyframe_every also works on the grid path: k-means keyframes (and frame 0) are kept whole for every query."""
    agg = model.aggregator
    rs = list(r) if isinstance(r, (list, tuple)) else [r] * DEPTH
    if layers == "flash":
        agg.global_start_idx, agg.global_end_idx = FLASH_RANGE
    elif isinstance(layers, int):
        agg.global_start_idx, agg.global_end_idx = (0 if early_sub else layers), (late_from - 1 if late_frame else DEPTH - 1)
    else:
        agg.global_start_idx, agg.global_end_idx = 0, DEPTH - 1
    for idx, blk in enumerate(agg.global_blocks):
        blk.attn.kv_downfactor = rs[idx]  # also read by the aggregator; >1 means "compressed"
        bsub = early_sub if (early_sub and isinstance(layers, int) and idx < layers) else sub
        if late_sub and idx >= late_from:
            bsub = late_sub
        if idx in full_layers and band_sub:
            bsub = band_sub
        elif idx in full_layers:
            bsub, rs[idx] = None, 1
            blk.attn.kv_downfactor = 1
        blk.attn.tf = dict(r=rs[idx], pool=pool, alpha=alpha, dedup=dedup, sub=tuple(bsub) if bsub else None,
                           diag=diag, mean=mean, nbr=nbr, nbr_mode=nbr_mode,
                           nbr_self=nbr_self, shift=shift, qsub=tuple(qsub) if (qsub and idx >= qsub_from) else None,
                           qsub_keep0=qsub_keep0, qsub_mode=qsub_mode,
                           wsel=wsel if (wsel and bsub and idx >= wsel_from) else None)
    agg.keyframe_every = keyframe_every or 10**9
    _KEYFRAME_EXTRA[:] = [int(i) for i in keyframe_extra]
    _KF_UNIF.update(every=int(keyframe_unif), kmeans=bool(kmeans), count=int(keyframe_count))


def budget_r(num_frames, budget_tokens, pH, pW, prefix=5, max_r=8):
    """Smallest r whose compressed key/value set fits in budget_tokens (r=1 means full attention)."""
    for r in range(1, max_r + 1):
        nk = num_frames * (prefix + (pH // r) * (pW // r)) if r > 1 else num_frames * (prefix + pH * pW)
        if nk <= budget_tokens:
            return r
    return max_r


def _compress(t, pH, pW, P0, r, pool):
    """t: [B, H, S*P, D] -> compressed spatial tokens [B, H, S, n, D] and prefix tokens [B, H, S, P0, D]."""
    B, Hh, N, D = t.shape
    P = P0 + pH * pW
    S = N // P
    t = t.view(B, Hh, S, P, D)
    prefix, spatial = t[:, :, :, :P0], t[:, :, :, P0:]
    spatial = spatial.reshape(B * Hh * S, pH, pW, D).permute(0, 3, 1, 2).float()
    nh, nw = pH // r, pW // r
    if pool == "avg":
        spatial = F.adaptive_avg_pool2d(spatial, (nh, nw))
    else:
        spatial = F.interpolate(spatial, size=(nh, nw), mode="nearest")
    spatial = spatial.to(t.dtype).permute(0, 2, 3, 1).reshape(B, Hh, S, nh * nw, D)
    return prefix, spatial, nh, nw


def _cell_logcount(pH, pW, nh, nw, device):
    """log of how many full-resolution tokens each pooled cell covers (adaptive pooling bins)."""
    def sizes(n_in, n_out):
        return torch.tensor([math.ceil((i + 1) * n_in / n_out) - (i * n_in) // n_out for i in range(n_out)],
                            dtype=torch.float32, device=device)
    return torch.log(torch.outer(sizes(pH, nh), sizes(pW, nw)).flatten())


def _descriptor_attention(self, x, pos=None, pH=None, pW=None, patch_start_idx=None, keyframe_indices=None):
    B, N, C = x.shape
    q, k, v = _project_qkv(self, x, pos)

    cfg = self.tf
    if cfg.get("sub") and pH is not None:
        assert B == 1, "batch size 1 only"
        kf = keyframe_indices[0].unique() if keyframe_indices is not None else None
        x = _grid_attention(self, x, q, k, v, pH, pW, patch_start_idx, cfg, kf)
    elif cfg["r"] > 1 and pH is not None:
        assert B == 1, "batch size 1 only"
        P0, r = patch_start_idx, cfg["r"]
        pk, sk, nh, nw = _compress(k, pH, pW, P0, r, cfg["pool"])
        pv, sv, _, _ = _compress(v, pH, pW, P0, r, cfg["pool"])
        S = sk.shape[2]
        kf = keyframe_indices[0].unique() if keyframe_indices is not None else torch.zeros(1, dtype=torch.long, device=x.device)
        others = torch.ones(S, dtype=torch.bool, device=x.device)
        if cfg["dedup"]:
            others[kf] = False
        # key/value set: prefix tokens of every frame, full-res patches of keyframes, descriptors of the other frames
        full_k = k.view(B, self.num_heads, S, -1, self.head_dim)[:, :, kf, P0:]
        full_v = v.view(B, self.num_heads, S, -1, self.head_dim)[:, :, kf, P0:]
        k_parts = [pk.flatten(2, 3), full_k.flatten(2, 3), sk[:, :, others].flatten(2, 3)]
        v_parts = [pv.flatten(2, 3), full_v.flatten(2, 3), sv[:, :, others].flatten(2, 3)]
        k, v = torch.cat(k_parts, 2), torch.cat(v_parts, 2)
        if cfg["alpha"] > 0:
            n_plain = k_parts[0].shape[2] + k_parts[1].shape[2]
            logc = _cell_logcount(pH, pW, nh, nw, x.device).repeat(int(others.sum()))
            bias = torch.cat([torch.zeros(n_plain, device=x.device), cfg["alpha"] * logc])
            x = _sdpa_key_bias(q, k, v, bias)
        else:
            x = F.scaled_dot_product_attention(q, k, v)
    else:
        x = F.scaled_dot_product_attention(q, k, v)

    x = x.transpose(1, 2).reshape(B, N, C)
    return self.proj_drop(self.proj(x))


MERGE_CHUNK = 16384  # tokens per step when merging the attention parts (bounds the temporaries)


def _autocast_dtype():
    return torch.get_autocast_dtype("cuda") if hasattr(torch, "get_autocast_dtype") else torch.get_autocast_gpu_dtype()


def _attn_lse(q, k, v):
    """SDPA (memory-efficient kernel, runs on T4) that also returns the log-sum-exp of the scaled logits per query."""
    o, lse = torch.ops.aten._scaled_dot_product_efficient_attention(q, k, v, None, True)[:2]
    return o, lse[..., :q.shape[-2]]


def _window_mask(score, pH, pW, sh, sw):
    """score [S, pH*pW] -> bool [S, pH*pW]: the highest-scoring patch of every sh x sw window (windows cut by the image
    border included), so each frame keeps exactly as many patches as the fixed grid [::sh, ::sw]."""
    S, dev = score.shape[0], score.device
    nh, nw = -(-pH // sh), -(-pW // sw)
    s = torch.full((S, nh * sh, nw * sw), -float("inf"), dtype=torch.float32, device=dev)
    s[:, :pH, :pW] = score.view(S, pH, pW).float()
    a = s.view(S, nh, sh, nw, sw).permute(0, 1, 3, 2, 4).reshape(S, nh, nw, sh * sw).argmax(-1)
    ii = torch.arange(nh, device=dev)[:, None] * sh + a // sw
    jj = torch.arange(nw, device=dev)[None] * sw + a % sw
    m = torch.zeros(S, pH, pW, dtype=torch.bool, device=dev)
    m[torch.arange(S, device=dev)[:, None, None], ii, jj] = True
    return m.view(S, -1)


def _prefix_mass(qp, k, lse, budget=32e6):
    """qp [1, H, nq, D] queries, k [1, H, n, D] keys, lse [1, H, nq] (log-sum-exp of each query over ALL keys) ->
    [n]: softmax mass every key receives, summed over queries and heads."""
    H, nq, D = qp.shape[1:]
    c = max(1, int(budget // (H * nq)))
    out = torch.empty(k.shape[2], dtype=torch.float32, device=k.device)
    for i in range(0, k.shape[2], c):
        lg = torch.matmul(qp[0], k[0, :, i:i + c].transpose(-1, -2)).float() * D ** -0.5
        out[i:i + c] = (lg - lse[0][..., None]).exp_().sum((0, 1))
    return out


def _key_score(q, k, v, S, P, P0, mode):
    """[S, pH*pW] patch-key scores for the content-adaptive grid (see configure, wsel)."""
    H, D = q.shape[1], q.shape[3]
    if mode == "norm":
        sc = k[0].float().norm(dim=-1).sum(0)
    else:
        qp = q.view(1, H, S, P, D)[:, :, :, :P0].reshape(1, H, S * P0, D).contiguous()
        _, lse = _attn_lse(qp, k, v)
        sc = _prefix_mass(qp, k, lse.float())
    return sc.view(S, P)[:, P0:]


def _frame_neighbours(x, S, P, P0, m, mode, whole, with_self=True):
    """[S, m] frame indices: each frame's m nearest frames (itself first if with_self), never a whole frame."""
    idx = torch.arange(S, device=x.device)
    if mode == "temporal":
        a = idx.float()
        score = -(a[:, None] - a[None]).abs()
    else:
        f = F.normalize(x.reshape(S, P, -1)[:, P0:].float().mean(1), dim=-1)
        score = f @ f.T
    score[idx, idx] = float("inf") if with_self else -float("inf")
    score[:, whole] = -float("inf")
    return score.topk(m, dim=1).indices


def _grid_attention(self, x, q, k, v, pH, pW, P0, cfg, kf=None):
    """Grid-subsampled global attention (AVGGT-style) with optional diagonal, mean fill, whole keyframes and
    neighbourhood resolution. All parts are disjoint key sets merged exactly into one softmax via their log-sum-exps."""
    # the raw efficient-attention op is not autocast-wrapped: on the unchunked projection path q/k come out in fp32 (from
    # the norm/RoPE) and v in half precision, so cast all three to the autocast dtype like SDPA under autocast would
    dt = _autocast_dtype() if torch.is_autocast_enabled() else v.dtype
    q, k, v = (t.to(dt).contiguous() for t in (q, k, v))
    _, H, N, D = q.shape
    P = P0 + pH * pW
    S = N // P
    qsel = anchor = None
    if cfg.get("qsub"):
        assert not cfg["nbr"], "query reduction is not combined with the neighbour pass"
        qh, qw = cfg["qsub"]
        qg = torch.zeros(pH, pW, dtype=torch.bool, device=q.device)
        qg[::qh, ::qw] = True
        selm = torch.ones(S, P, dtype=torch.bool, device=q.device)
        selm[:, P0:] = qg.flatten()
        ii = torch.arange(pH, device=q.device)[:, None]
        jj = torch.arange(pW, device=q.device)[None]
        win = ((ii - ii % qh) * pW + (jj - jj % qw)).flatten()  # patch index of each patch's window anchor
        anchor = torch.arange(N, device=q.device).view(S, P).clone()
        anchor[:, P0:] = torch.arange(S, device=q.device)[:, None] * P + P0 + win[None]
        if cfg.get("qsub_keep0"):
            selm[0] = True
            anchor[0] = torch.arange(P, device=q.device)
        qsel = selm.flatten().nonzero().squeeze(1)
        anchor = anchor.flatten()
    lse_mode = qsel is not None and cfg.get("qsub_mode") == "lse"
    if qsel is not None and not lse_mode:
        q = q[:, :, qsel].contiguous()
    Nq = q.shape[2]
    sh, sw = cfg["sub"]
    grid = torch.zeros(pH, pW, dtype=torch.bool, device=q.device)
    grid[::sh, ::sw] = True
    grid = grid.flatten()
    g_idx, ng_idx = grid.nonzero().squeeze(1), (~grid).nonzero().squeeze(1)
    # per-frame kept-patch mask; with `shift`, frame f keeps phase f mod (sh*sw) of every window, so a few consecutive
    # frames together cover every patch position (same number of keys as the fixed grid)
    gm = grid[None].repeat(S, 1)
    if cfg.get("shift"):
        assert not cfg["nbr"], "shifted grid is not combined with the neighbour pass"
        for f in range(S):
            ph = f % (sh * sw)
            g = torch.zeros(pH, pW, dtype=torch.bool, device=q.device)
            g[ph // sw::sh, ph % sw::sw] = True
            gm[f] = g.flatten()
    if cfg.get("wsel"):
        assert not cfg["nbr"] and qsel is None, "content-adaptive grid is not combined with nbr / query reduction"
        gm = _window_mask(_key_score(q, k, v, S, P, P0, cfg["wsel"]), pH, pW, sh, sw)
    whole = torch.zeros(S, dtype=torch.bool, device=q.device)
    whole[0] = True
    if kf is not None:
        whole[kf] = True
    w_idx, r_idx = whole.nonzero().squeeze(1), (~whole).nonzero().squeeze(1)  # whole frames, grid-reduced frames
    k4, v4 = k.reshape(H, S, P, D), v.reshape(H, S, P, D)

    def coarse(t4):  # camera/register tokens of every frame, whole frames, grid patches of the other frames
        return torch.cat([t4[:, :, :P0].reshape(H, -1, D), t4[:, w_idx, P0:].reshape(H, -1, D),
                          t4[:, r_idx, P0:][:, gm[r_idx]]], 1)[None]

    if lse_mode:  # shared coarse part computed at the window anchors only, then given to every token with its lse
        o_c, l_c = _attn_lse(q[:, :, qsel].contiguous(), coarse(k4), coarse(v4))
        terms = [(_expand(o_c, qsel, anchor, N), _expand(l_c[..., None], qsel, anchor, N)[..., 0].contiguous())]
        qsel = anchor = None
    else:
        terms = [_attn_lse(q, coarse(k4), coarse(v4))]
    scale = D ** -0.5
    if len(r_idx) == 0:
        return _expand(terms[0][0], qsel, anchor, N)
    if cfg["mean"]:
        km = k4[:, r_idx, P0:][:, ~gm[r_idx]].float().mean(1).to(q.dtype)  # [H, D]
        vm = v4[:, r_idx, P0:][:, ~gm[r_idx]].float().mean(1).to(v.dtype)
        s = (q[0] @ km[:, :, None]).squeeze(-1).float() * scale
        terms.append((vm[None, :, None], s[None]))
    if cfg["diag"]:
        dropped = torch.zeros(S, P, dtype=torch.bool, device=q.device)
        dropped[r_idx, P0:] = ~gm[r_idx]  # keys absent from the coarse set
        if cfg["nbr"] and cfg.get("nbr_self", True):
            dropped[:] = False  # own frame already whole in the neighbour pass
        ks, vs, dm = (k, v, dropped.flatten()) if qsel is None else (k[:, :, qsel], v[:, :, qsel], dropped.flatten()[qsel])
        s = torch.empty(1, H, Nq, dtype=torch.float32, device=q.device)
        for i in range(0, Nq, MERGE_CHUNK):  # no full-size q*k temporary
            s[..., i:i + MERGE_CHUNK] = (q[..., i:i + MERGE_CHUNK, :] * ks[..., i:i + MERGE_CHUNK, :]).sum(-1, dtype=torch.float32)
        terms.append((vs, (s * scale).masked_fill_(~dm, -float("inf"))))
    m = min(cfg["nbr"], len(r_idx) - (0 if cfg.get("nbr_self", True) else 1))
    if m > 0:
        nb = _frame_neighbours(x, S, P, P0, m, cfg["nbr_mode"], whole, cfg.get("nbr_self", True))
        k_ng, v_ng = k4[:, :, P0:][:, :, ng_idx], v4[:, :, P0:][:, :, ng_idx]  # [H, S, Pc, D]
        q4 = q.reshape(H, S, P, D)
        Pc = len(ng_idx)
        o2 = torch.empty(H, S, P, D, dtype=v.dtype, device=q.device)
        l2 = torch.empty(H, S, P, dtype=torch.float32, device=q.device)
        b = max(1, int(256e6 // (m * Pc * H * D * 2)))
        for i in range(0, S, b):
            n = nb[i:i + b]
            kb = k_ng[:, n].transpose(0, 1).reshape(len(n), H, m * Pc, D)
            vb = v_ng[:, n].transpose(0, 1).reshape(len(n), H, m * Pc, D)
            o, l = _attn_lse(q4[:, i:i + b].transpose(0, 1).contiguous(), kb, vb)
            o2[:, i:i + b], l2[:, i:i + b] = o.transpose(0, 1), l.transpose(0, 1)
        terms.append((o2.view(1, H, N, D), l2.view(1, H, N)))

    if len(terms) == 1:
        return _expand(terms[0][0], qsel, anchor, N)
    # out = sum_t softmax_t(lse) * o_t, written in place into the coarse output, token chunk by chunk
    out = terms[0][0]
    for i in range(0, Nq, MERGE_CHUNK):
        sl = slice(i, i + MERGE_CHUNK)
        ls = torch.stack([l[..., sl] for _, l in terms])
        w = torch.softmax(ls, 0).to(out.dtype)[..., None]
        acc = out[..., sl, :] * w[0]
        for (o, _), wt in zip(terms[1:], w[1:]):
            acc += (o if o.shape[-2] == 1 else o[..., sl, :]) * wt
        out[..., sl, :] = acc
    return _expand(out, qsel, anchor, N)


def _expand(out, qsel, anchor, N):
    """Query reduction: scatter the computed outputs back and give every other patch its window anchor's output."""
    if qsel is None:
        return out
    full = torch.empty(*out.shape[:2], N, out.shape[-1], dtype=out.dtype, device=out.device)
    full[:, :, qsel] = out
    return full[:, :, anchor]


def _project_qkv(self, x, pos):
    B, N, C = x.shape
    H, D = self.num_heads, self.head_dim

    def project(xs, ps):
        qkv = self.qkv(xs).reshape(xs.shape[0], xs.shape[1], 3, H, D).permute(2, 0, 3, 1, 4)
        q, k, v = qkv.unbind(0)
        q, k = self.q_norm(q), self.k_norm(k)
        if self.rope is not None:
            q, k = self.rope(q, ps), self.rope(k, ps)
        return q, k, v

    chunk = getattr(self, "qkv_chunk", 0)
    if not chunk or B * N <= chunk:
        return project(x, pos)
    dt = _autocast_dtype() if torch.is_autocast_enabled() else x.dtype
    q, k, v = (torch.empty(B, H, N, D, dtype=dt, device=x.device) for _ in range(3))
    if B > 1:  # frame attention: chunk over frames
        step = max(1, chunk // N)
        for i in range(0, B, step):
            for buf, t in zip((q, k, v), project(x[i:i + step], None if pos is None else pos[i:i + step])):
                buf[i:i + step] = t
    else:      # global attention: chunk over tokens
        for i in range(0, N, chunk):
            for buf, t in zip((q, k, v), project(x[:, i:i + chunk], None if pos is None else pos[:, i:i + chunk])):
                buf[:, :, i:i + chunk] = t
    return q, k, v


def _sdpa_key_bias(q, k, v, bias):
    """softmax(q k^T * scale + bias[key]) v without materializing a mask: the bias rides in one extra head dim,
    so the memory-efficient kernel still applies. Head dim is padded to a multiple of 8."""
    D = q.shape[-1]
    scale = D ** -0.5
    pad = 8
    qe = torch.zeros(*q.shape[:-1], pad, dtype=q.dtype, device=q.device)
    qe[..., 0] = 1
    ke = torch.zeros(*k.shape[:-1], pad, dtype=k.dtype, device=k.device)
    ke[..., 0] = (bias / scale).to(k.dtype)
    ve = torch.zeros(*v.shape[:-1], pad, dtype=v.dtype, device=v.device)
    out = F.scaled_dot_product_attention(torch.cat([q, qe], -1), torch.cat([k, ke], -1), torch.cat([v, ve], -1),
                                         scale=scale)
    return out[..., :D]
