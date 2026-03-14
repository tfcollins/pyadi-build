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
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "zed_fmcomms2",
            "--generate-script",
        ],
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


def test_hdl_build_docker_script_generation(cli_runner, tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: 2023_R2
build:
  runner: docker
platforms:
  zed_fmcomms2:
    arch: arm
    hdl_project: fmcomms2
    carrier: zed
    tool_version: 2023.2
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "zed_fmcomms2",
            "--generate-script",
            "--docker-image",
            "custom/vivado:2023.2",
        ],
    )

    assert result.exit_code == 0, result.output

    script_file = tmp_path / ".adibuild" / "work" / "build_hdl_arm.sh"
    content = script_file.read_text()
    assert "docker run --rm" in content
    assert "custom/vivado:2023.2" in content


def test_hdl_build_missing_args(cli_runner, tmp_path):
    """Test hdl build fails if no arguments provided."""

    result = cli_runner.invoke(cli, ["hdl", "build"])

    assert result.exit_code != 0
    assert (
        "You must specify either --platform OR both --project and --carrier"
        in result.output
    )


def test_hdl_build_power_report(cli_runner, tmp_path, mocker):
    """Test hdl build with --power-report flag."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

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
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "zed_fmcomms2",
            "--generate-script",
            "--power-report",
        ],
    )

    assert result.exit_code == 0

    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm.sh"
    content = script_file.read_text()

    assert "export ADI_GENERATE_XPA='1'" in content


def test_hdl_build_utilization_report(cli_runner, tmp_path, mocker):
    """Test hdl build with --utilization-report flag."""
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

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
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "hdl",
            "build",
            "-p",
            "zed_fmcomms2",
            "--generate-script",
            "--utilization-report",
        ],
    )

    assert result.exit_code == 0

    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_hdl_arm.sh"
    content = script_file.read_text()

    assert "export ADI_GENERATE_UTILIZATION='1'" in content


def test_hdl_build_caching(cli_runner, tmp_path, mocker):
    """Test hdl build caching logic."""
    # Ensure all Path.home() calls return the same tmp_path
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    
    # Mock source preparation to return a path and set self.repo and self.source_dir
    mock_repo = mocker.MagicMock()
    mock_repo.get_commit_sha.return_value = "abcdef1234567890"
    
    def side_effect_prep(self):
        self.repo = mock_repo
        self.source_dir = tmp_path / "source"
        return self.source_dir

    mocker.patch(
        "adibuild.projects.hdl.HDLBuilder.prepare_source",
        side_effect=side_effect_prep,
        autospec=True
    )

    # Mock toolchain and version checks
    mocker.patch("adibuild.projects.hdl.HDLBuilder._check_vivado_version", return_value="0")
    mocker.patch("adibuild.platforms.base.Platform.get_toolchain")
    mocker.patch("adibuild.core.executor.BuildExecutor.make")
    
    # Mock package_artifacts to create real dummy files in the output directory
    def side_effect_package(self, project_dir, hdl_project, carrier):
        output_dir = self.get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "system_top.bit").write_text("dummy bitstream")
        (output_dir / "system_top.xsa").write_text("dummy xsa")
        return {
            "artifacts": {
                "bit": [str(output_dir / "system_top.bit")],
                "xsa": [str(output_dir / "system_top.xsa")],
            },
            "output_dir": str(output_dir),
        }

    mocker.patch(
        "adibuild.projects.hdl.HDLBuilder.package_artifacts",
        side_effect=side_effect_package,
        autospec=True
    )

    # We need a real directory for the project to exist or mock the check
    (tmp_path / "source" / "projects" / "fmcomms2" / "zed").mkdir(parents=True, exist_ok=True)

    config_file = tmp_path / "config.yaml"
    config_file.write_text(f"""
project: hdl
repository: https://github.com/analogdevicesinc/hdl.git
tag: hdl_2023_r2
build:
  output_dir: {tmp_path / 'build'}
platforms:
  zed_fmcomms2:
    arch: arm
    hdl_project: fmcomms2
    carrier: zed
""")

    # First build - should NOT be cached
    result1 = cli_runner.invoke(
        cli, ["--config", str(config_file), "hdl", "build", "-p", "zed_fmcomms2"]
    )
    assert result1.exit_code == 0
    assert "HDL build pulled from cache" not in result1.output

    # Check cache directory exists and contains files
    cache_base = tmp_path / ".adibuild" / "cache" / "hdl"
    assert cache_base.exists()
    cache_dirs = list(cache_base.glob("*"))
    assert len(cache_dirs) == 1
    assert (cache_dirs[0] / "system_top.bit").exists()

    # Second build - should BE cached
    result2 = cli_runner.invoke(
        cli, ["--config", str(config_file), "hdl", "build", "-p", "zed_fmcomms2"]
    )
    assert result2.exit_code == 0
    assert "HDL build pulled from cache successfully" in result2.output
