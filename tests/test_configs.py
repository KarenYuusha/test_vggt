"""The configurations must stay exactly as they were when the results in results/ were produced."""
import json
from pathlib import Path

from tfvggt.configs import BUDGET_TOKENS, CONFIGS, RECOMMENDED, oracle_keyframes


def _norm(v):
    if isinstance(v, range):
        return {"__range__": [v.start, v.stop, v.step]}
    if isinstance(v, (tuple, list)):
        return [_norm(x) for x in v]
    if isinstance(v, dict):
        return {k: _norm(x) for k, x in sorted(v.items())}
    return v


def test_configs_match_snapshot():
    snap = json.loads((Path(__file__).parent / "configs_snapshot.json").read_text())
    assert BUDGET_TOKENS == snap["BUDGET_TOKENS"]
    now = {k: [w, _norm(kw)] for k, (w, kw) in CONFIGS.items()}
    assert set(now) == set(snap["CONFIGS"])
    for k in now:
        assert now[k] == snap["CONFIGS"][k], k


def test_recommended_exist():
    assert all(c in CONFIGS for c in RECOMMENDED)


def test_oracle_lists_packaged():
    assert isinstance(oracle_keyframes("rand", "fr1_360", 100), list)
