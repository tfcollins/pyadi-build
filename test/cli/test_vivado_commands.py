"""Tests for Vivado CLI commands."""

from pathlib import Path

from adibuild.cli.main import cli
from adibuild.core.toolchain import ToolchainInfo
from adibuild.core.vivado import VivadoInstallResult


def test_vivado_list_shows_supported_versions(cli_runner, mocker):
    installer = mocker.MagicMock()
    installer.list_supported_releases.return_value = [
        mocker.Mock(version="2023.2"),
        mocker.Mock(version="2025.1"),
    ]
    installer.status.side_effect = [None, None]
    mocker.patch("adibuild.core.vivado.VivadoInstaller", return_value=installer)

    result = cli_runner.invoke(cli, ["vivado", "list"])

    assert result.exit_code == 0
    assert "2023.2" in result.output
    assert "2025.1" in result.output
    assert "not installed" in result.output


def test_vivado_detect_displays_detected_toolchain(cli_runner, mocker):
    info = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vivado/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )
    installer = mocker.MagicMock()
    installer.status.return_value = info
    mocker.patch("adibuild.core.vivado.VivadoInstaller", return_value=installer)

    result = cli_runner.invoke(cli, ["vivado", "detect", "--version", "2023.2"])

    assert result.exit_code == 0
    assert "2023.2" in result.output
    assert "vivado" in result.output.lower()


def test_vivado_install_download_only(cli_runner, mocker, tmp_path):
    installer = mocker.MagicMock()
    installer.download_installer.return_value = tmp_path / "installer.bin"
    mocker.patch("adibuild.core.vivado.VivadoInstaller", return_value=installer)

    result = cli_runner.invoke(
        cli,
        [
            "vivado",
            "install",
            "--version",
            "2023.2",
            "--download-only",
            "--non-interactive",
        ],
        env={"AMD_USERNAME": "user", "AMD_PASSWORD": "pass"},
    )

    assert result.exit_code == 0
    installer.download_installer.assert_called_once()
    assert "Downloaded Vivado 2023.2 installer" in result.output


def test_vivado_install_calls_installer(cli_runner, mocker):
    toolchain = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vivado/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )
    installer = mocker.MagicMock()
    installer.install.return_value = VivadoInstallResult(
        release=mocker.Mock(version="2023.2"),
        installer_path=Path("/tmp/installer.bin"),
        extract_dir=Path("/tmp/extract"),
        toolchain=toolchain,
    )
    mocker.patch("adibuild.core.vivado.VivadoInstaller", return_value=installer)

    result = cli_runner.invoke(
        cli,
        ["vivado", "install", "--version", "2023.2", "--non-interactive"],
        env={"AMD_USERNAME": "user", "AMD_PASSWORD": "pass"},
    )

    assert result.exit_code == 0
    installer.install.assert_called_once()
    assert "Installed Vivado 2023.2" in result.output


def test_vivado_detect_errors_when_missing(cli_runner, mocker):
    installer = mocker.MagicMock()
    installer.status.return_value = None
    mocker.patch("adibuild.core.vivado.VivadoInstaller", return_value=installer)

    result = cli_runner.invoke(cli, ["vivado", "detect", "--version", "2023.2"])

    assert result.exit_code == 1
    assert "No installed Vivado toolchain detected" in result.output


def test_vivado_image_build_calls_manager(cli_runner, mocker):
    manager = mocker.MagicMock()
    manager.build_image.return_value = {
        "tag": "custom/vivado:2023.2",
        "version": "2023.2",
    }
    mocker.patch("adibuild.core.docker.VivadoDockerImageManager", return_value=manager)

    result = cli_runner.invoke(
        cli,
        [
            "vivado",
            "image",
            "build",
            "--version",
            "2023.2",
            "--tag",
            "custom/vivado:2023.2",
            "--non-interactive",
        ],
        env={"AMD_USERNAME": "user", "AMD_PASSWORD": "pass"},
    )

    assert result.exit_code == 0
    manager.build_image.assert_called_once()
    assert "custom/vivado:2023.2" in result.output


def test_vivado_image_list_calls_manager(cli_runner, mocker):
    manager = mocker.MagicMock()
    manager.list_images.return_value = [
        {
            "Repository": "adibuild/vivado",
            "Tag": "2023.2",
            "ID": "sha256:1234",
            "CreatedSince": "2 hours ago",
        }
    ]
    mocker.patch("adibuild.core.docker.VivadoDockerImageManager", return_value=manager)

    result = cli_runner.invoke(cli, ["vivado", "image", "list"])

    assert result.exit_code == 0
    assert "adibuild/vivado:2023.2" in result.output


def test_vivado_image_inspect_calls_manager(cli_runner, mocker):
    manager = mocker.MagicMock()
    manager.inspect_image.return_value = {"RepoTags": ["adibuild/vivado:2023.2"]}
    mocker.patch("adibuild.core.docker.VivadoDockerImageManager", return_value=manager)

    result = cli_runner.invoke(
        cli, ["vivado", "image", "inspect", "--tag", "adibuild/vivado:2023.2"]
    )

    assert result.exit_code == 0
    assert "RepoTags" in result.output
