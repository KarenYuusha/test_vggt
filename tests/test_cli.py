from tfvggt.cli import _configs, main


def test_config_groups():
    assert _configs(["recommended"])[0] == "B1"
    assert len(_configs(["all"])) > 70
    assert _configs(["B1", "recommended"]).count("B1") == 1


def test_configs_command(capsys):
    main(["configs"])
    assert "AVU-c40" in capsys.readouterr().out
