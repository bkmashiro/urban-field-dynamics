import urban_field_dynamics.cli as cli_module
from urban_field_dynamics.cli import main


def test_cli_exports_and_verifies_smoke_campaign(tmp_path, capsys) -> None:
    output = tmp_path / "smoke"

    assert main(["smoke", "--output", str(output)]) == 0
    assert "smoke-v1" in capsys.readouterr().out
    assert main(["verify", str(output)]) == 0
    assert "verified" in capsys.readouterr().out


def test_cli_exports_and_verifies_scaled_bounded_campaign(tmp_path, capsys) -> None:
    output = tmp_path / "bounded"

    assert (
        main(
            [
                "scaled-qualification",
                "--output",
                str(output),
                "--worlds",
                "1",
                "--end-year",
                "2026",
                "--workers",
                "1",
                "--source-revision",
                "deadbeef",
            ]
        )
        == 0
    )
    assert "exported bounded scaled-integrated-2026-canary-1" in capsys.readouterr().out
    assert main(["verify-bounded", str(output), "--workers", "1"]) == 0
    assert "verified bounded scaled-integrated-2026-canary-1" in capsys.readouterr().out


def test_cli_exports_and_verifies_scaled_policy_sweep(tmp_path, capsys) -> None:
    output = tmp_path / "sweep"

    assert (
        main(
            [
                "scaled-sweep",
                "--output",
                str(output),
                "--worlds",
                "1",
                "--end-year",
                "2028",
                "--workers",
                "1",
            ]
        )
        == 0
    )
    assert "scaled-p3-intensity-canary-1" in capsys.readouterr().out
    assert main(["verify-sweep", str(output), "--workers", "1"]) == 0
    assert "verified sweep" in capsys.readouterr().out


def test_cli_exports_and_verifies_scaled_stress_matrix(tmp_path, capsys) -> None:
    output = tmp_path / "stress"

    assert (
        main(
            [
                "scaled-stress",
                "--output",
                str(output),
                "--worlds",
                "1",
                "--end-year",
                "2026",
                "--workers",
                "1",
            ]
        )
        == 0
    )
    assert "exported stress matrix scaled-stress-2026-1" in capsys.readouterr().out

    assert main(["verify-stress", str(output), "--workers", "1"]) == 0
    assert "verified stress matrix scaled-stress-2026-1" in capsys.readouterr().out


def test_cli_labels_32_world_sweep_as_qualification(tmp_path, monkeypatch) -> None:
    observed: dict[str, str] = {}

    def fake_export(built, output, **_kwargs):
        observed["sweep_id"] = built.sweep_id
        return output

    monkeypatch.setattr(cli_module, "export_bounded_sweep", fake_export)
    assert (
        main(
            [
                "scaled-sweep",
                "--output",
                str(tmp_path / "sweep"),
                "--worlds",
                "32",
                "--end-year",
                "2026",
                "--workers",
                "1",
            ]
        )
        == 0
    )
    assert observed["sweep_id"] == "scaled-p3-intensity-qualification-32"
