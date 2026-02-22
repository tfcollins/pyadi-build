"""CLI tests for no-OS build commands."""

import pytest
from click.testing import CliRunner

from adibuild.cli.main import cli


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def noos_config_file(tmp_path):
    """Create a temporary valid no-OS config file."""
    config_file = tmp_path / "noos_config.yaml"
    config_file.write_text("""
project: noos
repository: https://github.com/analogdevicesinc/no-OS.git
tag: 2023_R2

build:
  parallel_jobs: 4
  output_dir: ./build

platforms:
  xilinx_ad9081:
    noos_platform: xilinx
    noos_project: ad9081_fmca_ebz
    iiod: false
    toolchain:
      preferred: vivado
      fallback: []

  stm32_ad9081:
    noos_platform: stm32
    noos_project: ad9081_fmca_ebz
    iiod: false
    toolchain:
      preferred: bare_metal
      fallback: []
""")
    return config_file


class TestNoOSCLI:
    def test_noos_help(self, cli_runner):
        """Test that noos group shows help."""
        result = cli_runner.invoke(cli, ["noos", "--help"])
        assert result.exit_code == 0
        assert "bare-metal" in result.output.lower() or "no-os" in result.output.lower()

    def test_noos_build_help(self, cli_runner):
        """Test that noos build subcommand shows help."""
        result = cli_runner.invoke(cli, ["noos", "build", "--help"])
        assert result.exit_code == 0
        assert "--platform" in result.output
        assert "--tag" in result.output
        assert "--generate-script" in result.output

    def test_noos_clean_help(self, cli_runner):
        """Test that noos clean subcommand shows help."""
        result = cli_runner.invoke(cli, ["noos", "clean", "--help"])
        assert result.exit_code == 0
        assert "--platform" in result.output
        assert "--deep" in result.output

    def test_noos_build_script_generation_xilinx(
        self, cli_runner, noos_config_file, mocker, tmp_path
    ):
        """Test generating a build script for no-OS Xilinx project."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(noos_config_file),
                "noos",
                "build",
                "-p",
                "xilinx_ad9081",
                "--generate-script",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify script file exists
        work_dir = tmp_path / ".adibuild" / "work"
        script_file = work_dir / "build_noos_bare_metal.sh"
        assert script_file.exists(), (
            f"Script file not found. Work dir contents: "
            f"{list(work_dir.iterdir()) if work_dir.exists() else 'not found'}"
        )

        content = script_file.read_text()
        assert "PLATFORM=xilinx" in content
        assert "NO-OS=" in content
        assert "make" in content

    def test_noos_build_script_has_iiod_flag(self, cli_runner, tmp_path, mocker):
        """Test that script includes IIOD flag."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project: noos
repository: https://github.com/analogdevicesinc/no-OS.git
tag: 2023_R2
build:
  parallel_jobs: 4
  output_dir: ./build
platforms:
  xilinx_ad9081:
    noos_platform: xilinx
    noos_project: ad9081_fmca_ebz
    iiod: true
    toolchain:
      preferred: vivado
      fallback: []
""")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "noos",
                "build",
                "-p",
                "xilinx_ad9081",
                "--generate-script",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        work_dir = tmp_path / ".adibuild" / "work"
        script_file = work_dir / "build_noos_bare_metal.sh"
        assert script_file.exists()
        content = script_file.read_text()
        assert "IIOD=y" in content

    def test_noos_build_script_with_profile(self, cli_runner, tmp_path, mocker):
        """Test that script includes PROFILE when specified."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project: noos
repository: https://github.com/analogdevicesinc/no-OS.git
tag: 2023_R2
build:
  parallel_jobs: 4
  output_dir: ./build
platforms:
  xilinx_ad9081:
    noos_platform: xilinx
    noos_project: ad9081_fmca_ebz
    profile: vcu118_ad9081_m8_l4
    iiod: false
    toolchain:
      preferred: vivado
      fallback: []
""")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(config_file),
                "noos",
                "build",
                "-p",
                "xilinx_ad9081",
                "--generate-script",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"

        work_dir = tmp_path / ".adibuild" / "work"
        script_file = work_dir / "build_noos_bare_metal.sh"
        content = script_file.read_text()
        assert "PROFILE=vcu118_ad9081_m8_l4" in content

    def test_noos_build_hardware_file_override(
        self, cli_runner, noos_config_file, mocker, tmp_path
    ):
        """Test that --hardware-file CLI arg overrides config."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        hw_file = tmp_path / "my_design.xsa"
        hw_file.write_text("dummy")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(noos_config_file),
                "noos",
                "build",
                "-p",
                "xilinx_ad9081",
                "--hardware-file",
                str(hw_file),
                "--generate-script",
            ],
        )

        # Should not error about the hardware file path (generate-script doesn't validate)
        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_noos_build_missing_platform_flag(self, cli_runner, noos_config_file):
        """Test that missing --platform flag causes error."""
        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(noos_config_file),
                "noos",
                "build",
            ],
        )
        # Should fail with missing required option
        assert result.exit_code != 0

    def test_noos_clean_script(self, cli_runner, noos_config_file, mocker, tmp_path):
        """Test clean command routes correctly to NoOSBuilder.clean."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        # Create the noos source dir so clean can find project
        noos_dir = tmp_path / ".adibuild" / "repos" / "noos"
        project_dir = noos_dir / "projects" / "ad9081_fmca_ebz"
        project_dir.mkdir(parents=True)

        # Mock executor.make so we don't actually run make
        mocker.patch("adibuild.core.executor.BuildExecutor.make")

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(noos_config_file),
                "noos",
                "clean",
                "-p",
                "xilinx_ad9081",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        assert "Clean completed" in result.output

    def test_noos_tag_auto_detects_tool_version(
        self, cli_runner, noos_config_file, mocker, tmp_path
    ):
        """Test that tag 2023_R2 auto-detects tool version 2023.2."""
        mocker.patch("pathlib.Path.home", return_value=tmp_path)

        mock_repo_cls = mocker.patch("adibuild.projects.noos.GitRepository")
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_commit_sha.return_value = "abc123def456"

        result = cli_runner.invoke(
            cli,
            [
                "--config",
                str(noos_config_file),
                "noos",
                "build",
                "-p",
                "xilinx_ad9081",
                "-t",
                "2023_R2",
                "--generate-script",
            ],
        )

        assert result.exit_code == 0, f"Command failed: {result.output}"
        # Auto-detection message should appear
        assert "2023.2" in result.output

    def test_noos_platform_dispatch_in_get_platform_instance(self, tmp_path):
        """Test that get_platform_instance correctly dispatches to NoOSPlatform."""
        from adibuild.cli.helpers import get_platform_instance
        from adibuild.core.config import BuildConfig
        from adibuild.platforms.noos import NoOSPlatform

        config = BuildConfig.from_dict(
            {
                "project": "noos",
                "repository": "https://github.com/analogdevicesinc/no-OS.git",
                "tag": "2023_R2",
                "build": {"parallel_jobs": 4},
                "platforms": {
                    "xilinx_ad9081": {
                        "noos_platform": "xilinx",
                        "noos_project": "ad9081_fmca_ebz",
                        "iiod": False,
                        "toolchain": {"preferred": "vivado"},
                    }
                },
            }
        )

        platform = get_platform_instance(config, "xilinx_ad9081")
        assert isinstance(platform, NoOSPlatform)
        assert platform.noos_platform == "xilinx"
