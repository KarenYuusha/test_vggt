"""TUM RGB-D (https://cvg.cit.tum.de/data/datasets/rgbd-dataset, CC BY 4.0), converted to the 7-Scenes layout.

Each RGB frame is paired with the nearest depth frame and ground-truth pose (|dt| <= 20 ms; unmatched frames dropped).
Output per frame: frame-XXXXXX.color.png, .depth.png (uint16 millimetres, 0 = invalid), .pose.txt (4x4 camera-to-world);
plus intrinsics.txt (fx fy cx cy of the Freiburg camera, no undistortion) and `done`.
The archive is read as a stream; only rgb/, depth/ and the three index files are extracted (member names are checked).
"""
import re
import shutil
import tarfile
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

URL = "https://cvg.cit.tum.de/rgbd/dataset/freiburg{f}/rgbd_dataset_freiburg{f}_{name}.tgz"
# short names used in results/ -> (camera, TUM sequence name). Any other sequence: "fr<camera>_<TUM name>".
SEQS = {"fr1_desk": (1, "desk"), "fr1_room": (1, "room"), "fr1_360": (1, "360"),
        "fr3_long_office": (3, "long_office_household"), "fr3_walking_xyz": (3, "walking_xyz"),
        "fr3_str_tex_far": (3, "structure_texture_far"),
        "fr1_rpy": (1, "rpy"), "fr1_plant": (1, "plant"), "fr1_teddy": (1, "teddy"),
        "fr2_360_hemisphere": (2, "360_hemisphere"), "fr2_desk": (2, "desk"),
        "fr3_sitting_halfsphere": (3, "sitting_halfsphere"),
        "fr1_desk2": (1, "desk2"), "fr1_floor": (1, "floor"), "fr1_xyz": (1, "xyz"), "fr3_cabinet": (3, "cabinet"),
        "fr2_rpy": (2, "rpy"), "fr2_360_kidnap": (2, "360_kidnap"), "fr2_pioneer_360": (2, "pioneer_360"),
        "fr3_sitting_rpy": (3, "sitting_rpy"), "fr3_walking_halfsphere": (3, "walking_halfsphere"),
        "fr2_xyz": (2, "xyz"),
        "fr3_walking_rpy": (3, "walking_rpy"), "fr2_pioneer_slam": (2, "pioneer_slam"),
        "fr2_large_with_loop": (2, "large_with_loop"),
        "fr3_nostr_tex_near_loop": (3, "nostructure_texture_near_withloop"), "fr3_teddy": (3, "teddy"),
        "fr2_desk_with_person": (2, "desk_with_person"),
        "fr3_sitting_xyz": (3, "sitting_xyz"), "fr3_str_tex_near": (3, "structure_texture_near"),
        "fr3_large_cabinet": (3, "large_cabinet"), "fr2_pioneer_slam2": (2, "pioneer_slam2"),
        "fr2_flowerbouquet": (2, "flowerbouquet"), "fr2_large_no_loop": (2, "large_no_loop"),
        "fr2_coke": (2, "coke"), "fr2_dishes": (2, "dishes"),
        "fr2_pioneer_slam3": (2, "pioneer_slam3"), "fr3_str_notex_near": (3, "structure_notexture_near"),
        "fr2_metallic_sphere2": (2, "metallic_sphere2")}
INTR = {1: (517.3, 516.5, 318.6, 255.3), 2: (520.9, 521.0, 325.1, 249.7), 3: (535.4, 539.2, 320.1, 247.6)}


def lookup(key):
    if key in SEQS:
        return SEQS[key]
    m = re.fullmatch(r"fr([123])_([a-z0-9_]+)", key)
    if not m:
        raise ValueError(f"unknown TUM sequence {key!r}: use a short name ({', '.join(sorted(SEQS))}) "
                         f"or fr<camera>_<TUM sequence name>, e.g. fr2_pioneer_slam3")
    return int(m.group(1)), m.group(2)


def _read_index(text):
    return [ln.split() for ln in text.splitlines() if ln.strip() and not ln.startswith("#")]


def quat_to_c2w(t, q):
    x, y, z, w = q
    R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                  [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                  [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = R, t
    return m


def _nearest(ts, arr):
    i = np.clip(np.searchsorted(arr, ts), 1, len(arr) - 1)
    j = np.where(np.abs(arr[i - 1] - ts) <= np.abs(arr[i] - ts), i - 1, i)
    return j, np.abs(arr[j] - ts)


def download(key, root):
    """Download and convert one sequence to <root>/tum/<key>/seq-01. Returns that folder."""
    f, name = lookup(key)
    out = Path(root) / "tum" / key / "seq-01"
    if (out / "done").exists():
        return out
    raw = Path(root) / "tum_raw" / key
    raw.mkdir(parents=True, exist_ok=True)
    print(f"[tfvggt] {key}: downloading {URL.format(f=f, name=name)}", flush=True)
    with urllib.request.urlopen(URL.format(f=f, name=name), timeout=60) as resp, \
            tarfile.open(fileobj=resp, mode="r|gz") as tar:
        for m in tar:
            parts = Path(m.name).parts
            if not m.isfile() or ".." in parts or len(parts) < 2:
                continue
            rel = Path(*parts[1:])
            if rel.parts[0] in ("rgb", "depth") and rel.suffix == ".png" or \
                    str(rel) in ("rgb.txt", "depth.txt", "groundtruth.txt"):
                dst = raw / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(m) as src, open(dst, "wb") as o:
                    shutil.copyfileobj(src, o)
    rgb = _read_index((raw / "rgb.txt").read_text())
    dep = _read_index((raw / "depth.txt").read_text())
    gt = _read_index((raw / "groundtruth.txt").read_text())
    dts = np.array([float(r[0]) for r in dep])
    gts = np.array([float(r[0]) for r in gt])
    out.mkdir(parents=True, exist_ok=True)
    k = 0
    for r in rgb:
        ts = float(r[0])
        di, dd = _nearest(ts, dts)
        gi, gd = _nearest(ts, gts)
        if dd > 0.02 or gd > 0.02:
            continue
        g = [float(x) for x in gt[gi][1:8]]
        stem = f"frame-{k:06d}"
        shutil.copy(raw / r[1], out / f"{stem}.color.png")
        d = np.asarray(Image.open(raw / dep[di][1]), dtype=np.float32) / 5.0  # 1/5000 m -> mm
        Image.fromarray(np.round(d).astype(np.uint16)).save(out / f"{stem}.depth.png")
        np.savetxt(out / f"{stem}.pose.txt", quat_to_c2w(g[:3], g[3:7]))
        k += 1
    (out / "intrinsics.txt").write_text(" ".join(map(str, INTR[f])))
    (out / "done").touch()
    shutil.rmtree(raw)
    print(f"[tfvggt] {key}: {k} frames of {len(rgb)} matched to depth and ground truth", flush=True)
    return out
