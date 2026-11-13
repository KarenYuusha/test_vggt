"""Run the one-cell notebook (notebooks/kaggle.ipynb) as Kaggle kernels from the command line. Optional: the notebook can
also simply be uploaded / pasted into Kaggle by hand.

    python tools/kaggle/kaggle_tool.py upload-code --user U [--public]        # code -> dataset U/tfvggt-src
    python tools/kaggle/kaggle_tool.py push  --user U --tag T --args "<tfvggt run args>" [--code U/tfvggt-src]
                                             [--data owner/dataset ...]
    python tools/kaggle/kaggle_tool.py watch --user U --tag T              # status, stalls, downloads the results
    python tools/kaggle/kaggle_tool.py status|delete --user U --tag T

Credentials: the usual Kaggle CLI ones (~/.kaggle/kaggle.json or KAGGLE_USERNAME / KAGGLE_KEY), or, for several
accounts, --accounts FILE (or $TFVGGT_KAGGLE_ACCOUNTS): one JSON object {"username": ..., "key": ...} per line.
Keys are passed to the Kaggle CLI through its environment only; they are never printed or written.
The Kaggle CLI is found as `kaggle` on PATH, or $KAGGLE_CLI. One kernel per account at a time.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILD = Path(__file__).resolve().parent / "build"


def _accounts(path):
    out = {}
    if path and Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("{"):
                d = json.loads(line)
                if isinstance(d, dict) and "username" in d and "key" in d:
                    out[d["username"]] = d["key"]
    return out


class Kaggle:
    def __init__(self, user, accounts_file=None):
        self.user = user
        self.cli = os.environ.get("KAGGLE_CLI") or shutil.which("kaggle")
        if not self.cli:
            sys.exit("Kaggle CLI not found: pip install kaggle, or set KAGGLE_CLI")
        acc = _accounts(accounts_file or os.environ.get("TFVGGT_KAGGLE_ACCOUNTS"))
        self.env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
        self.key = acc.get(user)
        if self.key:
            self.env.update(KAGGLE_USERNAME=user, KAGGLE_KEY=self.key)
            self.env.pop("KAGGLE_CONFIG_DIR", None)
        elif acc:
            sys.exit(f"account {user} not in the accounts file")

    def __call__(self, *args, timeout=None):
        try:
            r = subprocess.run([self.cli, *args], env=self.env, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=timeout)
            code, text = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired as e:
            code = -1
            text = "".join(x.decode("utf-8", "replace") if isinstance(x, bytes) else (x or "") for x in (e.stdout, e.stderr))
        return code, text.replace(self.key, "<key>") if self.key else text


def kernel_id(user, tag):
    return f"{user}/tfvggt-{tag}"


def upload_code(k, a):
    ds = a.dataset or f"{k.user}/tfvggt-src"
    d = BUILD / "code"
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    for name in ("pyproject.toml", "README.md"):
        shutil.copy(ROOT / name, d / name)
    shutil.copytree(ROOT / "src", d / "src", ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    meta = {"title": "tfvggt source", "id": ds, "licenses": [{"name": "other"}],
            "description": "Training-free faster VGGT inference: source of the tfvggt package (src/ + pyproject.toml)."}
    (d / "dataset-metadata.json").write_text(json.dumps(meta, indent=1))
    code, text = k("datasets", "status", ds)
    if code == 0 and "ready" in text.lower():
        code, text = k("datasets", "version", "-p", str(d), "-m", "update", "--dir-mode", "tar")
    else:
        code, text = k("datasets", "create", "-p", str(d), "--dir-mode", "tar", *(["--public"] if a.public else []))
    print(text.strip())
    for _ in range(40):  # a new version can take a minute or two to become usable
        if "ready" in k("datasets", "status", ds)[1].lower():
            print(f"{ds}: ready")
            return
        time.sleep(15)
    print(f"{ds}: not ready yet; check `kaggle datasets status {ds}` before pushing")


def push(k, a):
    nb = json.loads((ROOT / "notebooks" / "kaggle.ipynb").read_text(encoding="utf-8"))
    src = "".join(nb["cells"][0]["source"])
    src, n = re.subn(r'^ARGS = ".*"$', lambda _: f"ARGS = {json.dumps(a.args)}", src, count=1, flags=re.M)
    assert n == 1, "ARGS line not found in notebooks/kaggle.ipynb"
    nb["cells"][0]["source"] = src.splitlines(keepends=True)
    d = BUILD / a.tag
    shutil.rmtree(d, ignore_errors=True)
    d.mkdir(parents=True)
    (d / f"tfvggt-{a.tag}.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
    sources = [a.code or f"{k.user}/tfvggt-src"] + list(a.data)
    meta = {"id": kernel_id(k.user, a.tag), "title": f"tfvggt-{a.tag}", "code_file": f"tfvggt-{a.tag}.ipynb",
            "language": "python", "kernel_type": "notebook", "is_private": "true", "enable_gpu": "true",
            "enable_internet": "true", "machine_shape": "NvidiaTeslaT4", "dataset_sources": sources,
            "competition_sources": [], "kernel_sources": [], "model_sources": []}
    (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=1))
    print(k("kernels", "push", "-p", str(d), "--accelerator", "NvidiaTeslaT4")[1].strip())


def status(k, tag):
    m = re.search(r"KernelWorkerStatus\.([A-Z_]+)|status \"?([a-z_]+)", k("kernels", "status", kernel_id(k.user, tag))[1])
    return (m.group(1) or m.group(2)).upper() if m else "UNKNOWN"


def watch(k, a):
    """Print status changes; warn when QUEUED > 5 min or the log is silent > 5 min (restart rule); download on end."""
    kid, last, since, n_lines, quiet = kernel_id(k.user, a.tag), None, time.time(), 0, time.time()
    warned = set()
    while True:
        st = status(k, a.tag)
        if st != last:
            print(f"{kid}: {st}", flush=True)
            last, since = st, time.time()
        if st == "QUEUED" and time.time() - since > a.stall and "queued" not in warned:
            print(f"{kid}: QUEUED > {a.stall // 60} min, consider delete + push again", flush=True)
            warned.add("queued")
        if st == "RUNNING":
            lines = [ln for ln in k("kernels", "logs", "-f", kid, timeout=45)[1].splitlines() if ln.strip()]
            if len(lines) > n_lines:
                for ln in lines[n_lines:]:
                    m = re.search(r'"data":"(.*)"\}', ln)
                    text = m.group(1).replace("\\n", "") if m else ln
                    if "AUC30=" in text or "Traceback" in text or "Error" in text or "OOM" in text:
                        print(f"{kid}: {text[:160]}", flush=True)
                n_lines, quiet = len(lines), time.time()
                warned.discard("silent")
            elif time.time() - quiet > a.stall and "silent" not in warned:
                print(f"{kid}: log silent > {a.stall // 60} min, consider delete + push again", flush=True)
                warned.add("silent")
        if st in ("COMPLETE", "ERROR", "CANCEL_REQUESTED", "CANCEL_ACKNOWLEDGED", "CANCELLED"):
            break
        time.sleep(60)
    dest = Path(a.out) / a.tag
    dest.mkdir(parents=True, exist_ok=True)
    k("kernels", "output", kid, "-p", str(dest))
    rows = sum(1 for f in dest.rglob("*.jsonl") for ln in f.read_text().splitlines() if ln.strip())
    print(f"{kid}: {st}, {rows} result rows in {dest}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["upload-code", "push", "watch", "status", "delete"])
    ap.add_argument("--user", required=True)
    ap.add_argument("--accounts", help="JSON-lines accounts file (several Kaggle accounts)")
    ap.add_argument("--tag", help="kernel name suffix: <user>/tfvggt-<tag>")
    ap.add_argument("--args", default="--dataset tum:fr1_xyz --frames 50 --configs recommended",
                    help="arguments of `tfvggt run` written into the notebook")
    ap.add_argument("--code", help="code dataset (default <user>/tfvggt-src)")
    ap.add_argument("--dataset", help="upload-code: dataset id (default <user>/tfvggt-src)")
    ap.add_argument("--data", nargs="*", default=[], help="extra datasets to attach (prepared sequences)")
    ap.add_argument("--public", action="store_true", help="upload-code: make the code dataset public")
    ap.add_argument("--out", default=str(ROOT / "results" / "kaggle"), help="watch: where results are downloaded")
    ap.add_argument("--stall", type=int, default=300, help="watch: seconds before warning about a stall")
    a = ap.parse_args()
    k = Kaggle(a.user, a.accounts)
    if a.cmd in ("push", "watch", "status", "delete") and not a.tag:
        sys.exit("--tag is required")
    if a.cmd == "upload-code":
        upload_code(k, a)
    elif a.cmd == "push":
        push(k, a)
    elif a.cmd == "watch":
        watch(k, a)
    elif a.cmd == "status":
        print(status(k, a.tag))
    elif a.cmd == "delete":
        print(k("kernels", "delete", kernel_id(k.user, a.tag), "-y")[1].strip())


if __name__ == "__main__":
    main()
