from adibuild.cli.main import cli


def test_hdl_build_with_ignore_check(cli_runner, tmp_path, mocker):
    """Test hdl build with --ignore-version-check flag."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
platforms:
  test_plat:
    hdl_project: test
    carrier: test
    arch: arm
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "test_plat",
            "--generate-script",
            "--ignore-version-check",
        ],
    )

    assert result.exit_code == 0
    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm.sh"
    content = script_file.read_text()

    assert "export ADI_IGNORE_VERSION_CHECK='1'" in content


def test_hdl_build_without_ignore_check(cli_runner, tmp_path, mocker):
    """Test hdl build without flag (should not set env var in script mode)."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
platforms:
  test_plat:
    hdl_project: test
    carrier: test
    arch: arm
""")

    result = cli_runner.invoke(
        cli, ["--config", str(config_file), "hdl", "build", "-p", "test_plat", "--generate-script"]
    )

    assert result.exit_code == 0
    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm.sh"
    content = script_file.read_text()

    assert "ADI_IGNORE_VERSION_CHECK" not in content
