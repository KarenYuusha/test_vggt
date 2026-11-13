"""Microsoft 7-Scenes (https://www.microsoft.com/en-us/research/project/rgb-d-dataset-7-scenes/).

Microsoft distributes it for non-commercial research. It is downloaded on the machine that runs the code and never
redistributed by this project. Only the requested sequence is read from each scene archive (HTTP range requests).
Layout: <root>/7scenes/<scene>/<seq>/frame-XXXXXX.{color.png,depth.png,pose.txt}
"""
import io
import shutil
import zipfile
from pathlib import Path

URL = "http://download.microsoft.com/download/2/8/5/28564B23-0828-408F-8631-23B1EFF1DAC8/{}.zip"
SCENES = ["chess", "fire", "heads", "office", "pumpkin", "redkitchen", "stairs"]


def _seqs(z, scene, name):
    return [f"seq-{int(x.lower().replace('sequence', '')):02d}" for x in z.read(f"{scene}/{name}").decode().split()]


def sequence_order(scene):
    """The scene's sequences, test split first then train split (the order the experiments took them in)."""
    from remotezip import RemoteZip
    with RemoteZip(URL.format(scene)) as z:
        return _seqs(z, scene, "TestSplit.txt") + _seqs(z, scene, "TrainSplit.txt")


def download(scene, seq, root):
    """Download <scene>/<seq> (e.g. office, seq-06) to <root>/7scenes/<scene>/<seq>. Returns that folder.
    seq may also be an index into sequence_order(scene): 0 = first test sequence."""
    from remotezip import RemoteZip
    if scene not in SCENES:
        raise ValueError(f"unknown 7-Scenes scene {scene!r}; one of {SCENES}")
    if isinstance(seq, int):
        seq = sequence_order(scene)[seq]
    out = Path(root) / "7scenes" / scene / seq
    if (out / "done").exists():
        return out
    print(f"[tfvggt] 7scenes {scene}/{seq}: downloading", flush=True)
    for attempt in range(5):  # the Microsoft server drops long range reads now and then
        try:
            with RemoteZip(URL.format(scene)) as z:
                inner = io.BytesIO(z.read(f"{scene}/{seq}.zip"))
            break
        except Exception as e:  # noqa: BLE001
            print(f"[tfvggt] {scene}/{seq}: attempt {attempt + 1} failed ({type(e).__name__}), retrying", flush=True)
    else:
        raise RuntimeError(f"{scene}/{seq}: download failed 5 times")
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(inner) as zi:
        for info in zi.infolist():
            name = Path(info.filename).name
            if name.endswith((".color.png", ".depth.png", ".pose.txt")):
                with zi.open(info) as src, open(out / name, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    (out / "done").touch()
    print(f"[tfvggt] 7scenes {scene}/{seq}: {len(list(out.glob('*.pose.txt')))} frames", flush=True)
    return out
