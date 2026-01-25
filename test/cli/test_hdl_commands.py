from adibuild.cli.main import cli


def test_hdl_build_script_generation(cli_runner, tmp_path, mocker):
    """Test generating a build script for HDL project."""

    # Mock home directory
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Create a config file defining the platform
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
platforms:
  zed_fmcomms2:
    arch: arm
    hdl_project: fmcomms2
    carrier: zed
    make_variables:
      RX_LANE_RATE: 2.5
""")

    result = cli_runner.invoke(
        cli,
        ["--config", str(config_file), "hdl", "build", "-p", "zed_fmcomms2", "--generate-script"],
    )

    assert result.exit_code == 0, f"Command failed: {result.output}"

    # Verify script file exists
    work_dir = tmp_path / ".adibuild" / "work"
    # Script name: build_<project>_<arch>.sh -> build_hdl_arm.sh
    script_file = work_dir / "build_hdl_arm.sh"

    assert script_file.exists()
    content = script_file.read_text()

    assert "git clone" in content
    assert "projects/fmcomms2/zed" in content
    assert "RX_LANE_RATE=2.5" in content

    # Check for artifact copy commands (generic find)
    assert "find" in content
    assert "*.xsa" in content
    assert "*.bit" in content


def test_hdl_build_clean(cli_runner, tmp_path, mocker):
    """Test hdl build with clean flag (script generation to verify clean command)."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
platforms:
  zcu102_daq2:
    arch: arm64
    hdl_project: daq2
    carrier: zcu102
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "zcu102_daq2",
            "--clean",
            "--generate-script",
        ],
    )

    assert result.exit_code == 0

    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm64.sh"
    content = script_file.read_text()

    assert "make" in content
    assert "clean" in content
    assert "-C" in content


def test_hdl_build_dynamic_args(cli_runner, tmp_path, mocker):
    """Test hdl build using --project and --carrier dynamic arguments."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Create a config file just for repo URL, no platform definitions
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "--project",
            "fmcomms2",
            "--carrier",
            "zed",
            "--arch",
            "arm",
            "--generate-script",
        ],
    )

    assert result.exit_code == 0, f"Command failed: {result.output}"

    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm.sh"

    assert script_file.exists()
    content = script_file.read_text()

    assert "projects/fmcomms2/zed" in content


def test_hdl_build_missing_args(cli_runner, tmp_path):
    """Test hdl build fails if no arguments provided."""

    result = cli_runner.invoke(cli, ["hdl", "build"])

    assert result.exit_code != 0
    assert "You must specify either --platform OR both --project and --carrier" in result.output
