import pytest

from tfvggt.datasets import resolve, sequences_in
from tfvggt.datasets.tum import lookup


def test_tum_names():
    assert lookup("fr3_str_tex_near") == (3, "structure_texture_near")
    assert lookup("fr2_pioneer_slam3") == (2, "pioneer_slam3")
    assert lookup("fr1_some_new_sequence") == (1, "some_new_sequence")
    with pytest.raises(ValueError):
        lookup("not_a_tum_name")


def test_bad_spec():
    with pytest.raises(ValueError):
        resolve("kitti:00")


def test_prepared_folder(tmp_path):
    (tmp_path / "office" / "seq-06").mkdir(parents=True)
    (tmp_path / "office" / "seq-06" / "done").touch()
    (tmp_path / "chess" / "seq-01").mkdir(parents=True)  # not finished: ignored
    assert [p.name for p in sequences_in(tmp_path)] == ["seq-06"]
    assert sequences_in(tmp_path, ["chess"]) == []
