"""Named attention configurations: name -> (weights, keyword arguments of tfvggt.core.configure).

Every configuration used in the experiments (results/) is kept, under the same name, so old result rows stay comparable.
Recommended ones are listed in RECOMMENDED; `tfvggt configs` prints them all.
"""
import json
from importlib import resources

# name: (weights, configure kwargs); "budget" means r is picked from the number of frames
CONFIGS = {
    "B1": ("vggt", dict(r=1)),                                                   # full attention (+exact opts)
    "E1-flash": ("vggt", dict(r=3, layers="flash", dedup=False)),                 # FlashVGGT layout, no training
    "E1-all": ("vggt", dict(r=3, dedup=False)),                                   # compress every global layer
    "E2-all": ("vggt", dict(r=3, alpha=1.0)),                                     # + mass correction
    "E2-a05": ("vggt", dict(r=3, alpha=0.5)),
    "E2-avg": ("vggt", dict(r=3, alpha=1.0, pool="avg")),
    "E3-budget": ("vggt", dict(r="budget", alpha=1.0)),
    "E2-flash": ("vggt", dict(r=3, layers="flash", alpha=1.0)),
    "E1-all-r2": ("vggt", dict(r=2, dedup=False)),
    "E2-all-r2": ("vggt", dict(r=2, alpha=1.0)),
    "E1-all-r4": ("vggt", dict(r=4, dedup=False)),
    "E2-all-r4": ("vggt", dict(r=4, alpha=1.0)),
    # extra full-res keyframes from FlashVGGT's k-means on DINO frame tokens (S // 10 clusters + frame 0), no mass correction
    "K-r2k10": ("vggt", dict(r=2, dedup=False, keyframe_every=10)),
    "K-r3k10": ("vggt", dict(r=3, dedup=False, keyframe_every=10)),
    # AVGGT (CVPR 2026) reproduction: global layers 0-8 as frame attention, grid K/V subsampling (frame 0 whole),
    # diagonal preservation, mean fill. sigma = sh*sw.
    "AV-s4": ("vggt", dict(r=4, layers=9, sub=(2, 2), diag=True, mean=True)),
    "AV-s9": ("vggt", dict(r=9, layers=9, sub=(3, 3), diag=True, mean=True)),
    "AV-s16": ("vggt", dict(r=16, layers=9, sub=(4, 4), diag=True, mean=True)),
    # this work: neighbourhood resolution, each frame sees its m most similar frames whole, the rest on the grid
    "NB-s9m4": ("vggt", dict(r=9, layers=9, sub=(3, 3), mean=True, nbr=4)),
    "NB-s16m4": ("vggt", dict(r=16, layers=9, sub=(4, 4), mean=True, nbr=4)),
    "NB-s9m2": ("vggt", dict(r=9, layers=9, sub=(3, 3), mean=True, nbr=2)),
    "NB-s9m8": ("vggt", dict(r=9, layers=9, sub=(3, 3), mean=True, nbr=8)),
    "NB-s9m4t": ("vggt", dict(r=9, layers=9, sub=(3, 3), mean=True, nbr=4, nbr_mode="temporal")),
    "NB-s9m4-nomean": ("vggt", dict(r=9, layers=9, sub=(3, 3), nbr=4)),
    "NBx-s9m3": ("vggt", dict(r=9, layers=9, sub=(3, 3), diag=True, mean=True, nbr=3, nbr_self=False)),
    "AV-s4-g0": ("vggt", dict(r=4, layers="all", sub=(2, 2), diag=True, mean=True)),
    # AVGGT + whole k-means keyframes (coverage anchors, this work)
    "AVK-s4k10": ("vggt", dict(r=4, layers=9, sub=(2, 2), diag=True, mean=True, keyframe_every=10)),
    "AVK-s9k10": ("vggt", dict(r=9, layers=9, sub=(3, 3), diag=True, mean=True, keyframe_every=10)),
    "AVK-s9k5": ("vggt", dict(r=9, layers=9, sub=(3, 3), diag=True, mean=True, keyframe_every=5)),
    # ablations of what makes K-r2k10 robust on stairs/heads (all 24 layers global, nearest r=2, no diag/mean)
    "G-s4": ("vggt", dict(r=4, layers="all", sub=(2, 2))),
    "AV-s4-nodm": ("vggt", dict(r=4, layers=9, sub=(2, 2))),
    "AVE-s4e36-nodm": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6))),
    # per-frame shifted grid phase (this work): same key count as AVGGT, every patch position kept in some frame
    "AVS-s4": ("vggt", dict(r=4, layers=9, sub=(2, 2), diag=True, mean=True, shift=True)),
    "AVS-s9": ("vggt", dict(r=9, layers=9, sub=(3, 3), diag=True, mean=True, shift=True)),
    "AVES-s4e36": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, shift=True)),
    "AVES-s9e36": ("vggt", dict(r=9, layers=9, sub=(3, 3), early_sub=(6, 6), diag=True, mean=True, shift=True)),
    "AVEK-s4e36k10": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   keyframe_every=10)),
    "AVEK-s4e36k20": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   keyframe_every=20)),
    # query-side reduction (this work): global attention computed on a sparse query grid, other patches reuse their
    # window's update; on top of AVE-s4e36
    "Q-q4": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2))),
    "Q-q4k0": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2),
                            qsub_keep0=True)),
    "Q-q4L13": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2),
                             qsub_from=13)),
    "Q-q4L17": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2),
                             qsub_from=17)),
    "Q-q9": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(3, 3))),
    "Q-q4lse": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2),
                             qsub_mode="lse")),
    "Q-q4lseL9": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, qsub=(2, 2),
                               qsub_mode="lse", qsub_from=9)),
    # cheaper late layers on top of AVE-s4e36: coarser grid, or frame attention, for global layers 17-23
    "AVEL16": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, late_sub=(4, 4))),
    "AVEL36": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, late_sub=(6, 6))),
    "AVEL16f13": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, late_sub=(4, 4),
                               late_from=13)),
    "AVELF": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, late_frame=True)),
    # early global layers kept cross-frame on a very coarse grid instead of frame attention (this work)
    "AVE-s4e36": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True)),
    # ablation (TUM fr1_360 / fr1_room drop): which part of the compression hurts?
    "ABL-e36-Lfull": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   full_layers=range(9, 24))),           # only layers 0-8 compressed (6x6 grid)
    "ABL-Efull-s4": ("vggt", dict(r=4, layers="all", sub=(2, 2), diag=True, mean=True,
                                  full_layers=range(9))),                # only layers 9-23 compressed (s4 grid)
    "ABL-Efull-s4k10": ("vggt", dict(r=4, layers="all", sub=(2, 2), diag=True, mean=True, keyframe_every=10,
                                     full_layers=range(9))),
    "AVEK-s4e36k5": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                  keyframe_every=5)),
    # AVE / AVEK + full attention in global layers 14-18 (band found by the ablation, results/ablation_plan.md)
    "AVEB-s4e36f14": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   full_layers=range(14, 19))),
    "AVEKB-s4e36k10f14": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                       keyframe_every=10, full_layers=range(14, 19))),
    # cheaper bands (results/narrow_plan.md): 3 full layers, or layers 14-18 on a 1x2 grid (half the patch keys)
    "AVEKB-f15n3": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                 keyframe_every=10, full_layers=range(15, 18))),
    "AVEKB-f14n3": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                 keyframe_every=10, full_layers=range(14, 17))),
    "AVEKB-f16n3": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                 keyframe_every=10, full_layers=range(16, 19))),
    "AVEKB-g12": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                               keyframe_every=10, full_layers=range(14, 19), band_sub=(1, 2))),
    # oracle repair (results/rotation_plan.md): AVEK + the 10% frames that AVEK breaks most (picked with ground truth),
    # or + the same number of random frames; per-sequence lists in scripts/oracle_keyframes.json
    "AVEK-oracle": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                 keyframe_every=10, keyframe_extra="oracle")),
    "AVEK-rand": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                               keyframe_every=10, keyframe_extra="rand")),
    # uniform-in-time extra keyframes (results/kfx_plan.md): + S//10 frames spread evenly in time, kept whole
    "AVEKU-u10": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                               keyframe_every=10, keyframe_unif=10)),
    "AVEKBU-f16u10": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   keyframe_every=10, full_layers=range(16, 19), keyframe_unif=10)),
    # no k-means: frame 0 + S//5 frames spread evenly in time (same number of whole frames as AVEKU-u10)
    "AVU-u5": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                            keyframe_every=10, keyframe_unif=5, kmeans=False)),
    # long sequences (results/longkf_plan.md): frame 0 + a fixed 40 frames spread evenly in time (= S//5 at N=200)
    "AVU-c40": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                             keyframe_every=10, keyframe_count=40, kmeans=False)),
    # which band of the late layers needs full cross-frame attention?
    "ABL-L9-13full": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                   full_layers=range(9, 14))),
    "ABL-L14-18full": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                    full_layers=range(14, 19))),
    "ABL-L19-23full": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True,
                                    full_layers=range(19, 24))),
    # content-adaptive grid in layers 9-23 (best patch of each 2x2 window instead of the first)
    "AVEW-pref": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, wsel="pref")),
    "AVEW-norm": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, wsel="norm")),
    "AVEKW-pref": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(6, 6), diag=True, mean=True, wsel="pref",
                                keyframe_every=10)),
    "AVE-s4e16": ("vggt", dict(r=4, layers=9, sub=(2, 2), early_sub=(4, 4), diag=True, mean=True)),
    "AVE-s9e36": ("vggt", dict(r=9, layers=9, sub=(3, 3), early_sub=(6, 6), diag=True, mean=True)),
    "AVEK-s9e36k10": ("vggt", dict(r=9, layers=9, sub=(3, 3), early_sub=(6, 6), diag=True, mean=True,
                                   keyframe_every=10)),
    "Ref-flash": ("flash", dict(r=3, layers="flash", dedup=False)),               # fine-tuned FlashVGGT
    "Ref-flash-mass": ("flash", dict(r=3, layers="flash", alpha=1.0)),
}
BUDGET_TOKENS = 10 * 893  # key/value budget = 10 full frames

# the configurations README.md recommends (section "Chọn cấu hình")
RECOMMENDED = ["B1", "AVE-s4e36", "AVU-c40", "AVEK-s4e36k10", "AVEKB-f16n3", "AVU-u5", "AVEKBU-f16u10"]


def oracle_keyframes(name, scene, n):
    """Extra-keyframe lists of the oracle diagnostic (keyframe_extra="oracle" / "rand"), shipped in assets/."""
    lists = json.loads(resources.files("tfvggt").joinpath("assets/oracle_keyframes.json").read_text())
    return lists[name][f"{scene}__{n}"]
