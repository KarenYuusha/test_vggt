import torch

from tfvggt.core import _KF_UNIF, _select_keyframes_extra, uniform_extra


def test_uniform_extra_centres():
    assert uniform_extra(100, 5, {0}) == [10, 30, 50, 70, 90]


def test_uniform_extra_moves_off_taken_frames():
    out = uniform_extra(20, 2, {5, 15})
    assert len(set(out)) == 2 and not ({5, 15} & set(out))
    assert all(abs(a - b) <= 1 for a, b in zip(out, [5, 15]))


def test_fixed_count_without_kmeans():
    old = dict(_KF_UNIF)
    try:
        _KF_UNIF.update(every=0, kmeans=False, count=40)
        tokens = torch.zeros(800 * 2, 4)
        idx = _select_keyframes_extra(tokens, 1, 800, 2, 4)
        assert idx.shape == (1, 41) and idx[0, 0] == 0  # frame 0 + 40 evenly spread frames
        _KF_UNIF.update(count=40)
        idx = _select_keyframes_extra(torch.zeros(30 * 2, 4), 1, 30, 2, 4)
        assert idx.shape == (1, 30)  # capped at S - 1 extras
    finally:
        _KF_UNIF.clear()
        _KF_UNIF.update(old)
