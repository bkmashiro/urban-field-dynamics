from urban_field_dynamics.cli import main


def test_cli_exports_and_verifies_smoke_campaign(tmp_path, capsys) -> None:
    output = tmp_path / "smoke"

    assert main(["smoke", "--output", str(output)]) == 0
    assert "smoke-v1" in capsys.readouterr().out
    assert main(["verify", str(output)]) == 0
    assert "verified" in capsys.readouterr().out
