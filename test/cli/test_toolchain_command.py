"""Tests for toolchain detection command."""

from pathlib import Path

from adibuild.cli.main import cli
from adibuild.core.toolchain import ToolchainInfo


def test_toolchain_detect_all(cli_runner, mock_toolchain_all, mocker):
    """Test toolchain command when all toolchains are detected."""
    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 0
    assert "Detecting available toolchains" in result.output
    assert "Vivado" in result.output
    assert "2023.2" in result.output
    assert "ARM GNU Toolchain" in result.output or "ARM" in result.output
    assert "System" in result.output


def test_toolchain_vivado_only(cli_runner, mock_toolchain_vivado):
    """Test toolchain command when only Vivado is detected."""
    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 0
    assert "Vivado" in result.output
    assert "2023.2" in result.output
    # Should show that others are not found
    assert "not found" in result.output or "auto-download" in result.output


def test_toolchain_none_found(cli_runner, mock_toolchain_none):
    """Test toolchain command when no toolchains are detected."""
    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 0
    assert "Detecting available toolchains" in result.output
    assert "not found" in result.output
    # Should suggest auto-download for ARM toolchain
    assert "auto-download" in result.output


def test_toolchain_platform_specific_zynqmp(cli_runner, mock_toolchain_vivado, mocker, tmp_path):
    """Test toolchain command for specific platform (zynqmp)."""
    # Mock config loading
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynqmp": {
                "arch": "arm64",
                "cross_compile": "aarch64-linux-gnu-",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
            }
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    # Mock platform instance
    mock_platform = mocker.MagicMock()
    mock_platform.get_toolchain.return_value = mock_toolchain_vivado
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    result = cli_runner.invoke(cli, ["toolchain", "-p", "zynqmp"])

    assert result.exit_code == 0
    assert "zynqmp" in result.output.lower()
    # Should show selected toolchain
    assert "Selected" in result.output or "Vivado" in result.output


def test_toolchain_platform_specific_zynq(cli_runner, mock_toolchain_vivado, mocker):
    """Test toolchain command for specific platform (zynq)."""
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynq": {
                "arch": "arm",
                "cross_compile": "arm-linux-gnueabihf-",
                "defconfig": "zynq_xcomm_adv7511_defconfig",
                "kernel_target": "uImage",
            }
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    mock_platform = mocker.MagicMock()
    mock_platform.get_toolchain.return_value = mock_toolchain_vivado
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    result = cli_runner.invoke(cli, ["toolchain", "-p", "zynq"])

    assert result.exit_code == 0
    assert "zynq" in result.output.lower()


def test_toolchain_detection_failure(cli_runner, mocker):
    """Test toolchain command when detection raises exception."""
    # Mock all toolchain detections to raise exceptions
    mocker.patch(
        "adibuild.core.toolchain.VivadoToolchain.detect", side_effect=Exception("Detection error")
    )
    mocker.patch("adibuild.core.toolchain.ArmToolchain.detect", return_value=None)
    mocker.patch("adibuild.core.toolchain.SystemToolchain.detect", return_value=None)

    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 1
    assert "Toolchain detection failed" in result.output or "Error" in result.output


def test_toolchain_with_custom_config(cli_runner, mock_toolchain_vivado, mock_config_file, mocker):
    """Test toolchain command with custom config file."""
    from adibuild.core.config import BuildConfig

    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "platforms": {
            "zynqmp": {
                "arch": "arm64",
                "cross_compile": "aarch64-linux-gnu-",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
            }
        },
    }

    config = BuildConfig.from_dict(config_data)
    mocker.patch("adibuild.core.config.BuildConfig.from_yaml", return_value=config)

    mock_platform = mocker.MagicMock()
    mock_platform.get_toolchain.return_value = mock_toolchain_vivado
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    result = cli_runner.invoke(
        cli, ["--config", str(mock_config_file), "toolchain", "-p", "zynqmp"]
    )

    assert result.exit_code == 0
    # Should use the custom config
    assert "zynqmp" in result.output.lower()


def test_toolchain_invalid_platform(cli_runner):
    """Test toolchain command with invalid platform."""
    result = cli_runner.invoke(cli, ["toolchain", "-p", "invalid"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid" in result.output.lower()


def test_toolchain_display_format(cli_runner, mock_toolchain_all):
    """Test that toolchain command displays information in readable format."""
    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 0
    # Should have nice formatting with checkmarks or symbols
    # (The actual symbols might vary, but the structure should be there)
    assert "Detecting" in result.output
    assert "Toolchain" in result.output


def test_toolchain_mixed_detection(cli_runner, mocker):
    """Test toolchain command with mixed detection (some found, some not)."""
    # Vivado found, ARM not found, System found
    vivado_info = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vitis/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )

    system_info = ToolchainInfo(
        type="system",
        version="11.4.0",
        path=None,
        env_vars={},
        cross_compile_arm32=None,
        cross_compile_arm64="aarch64-linux-gnu-",
    )

    mocker.patch("adibuild.core.toolchain.VivadoToolchain.detect", return_value=vivado_info)
    mocker.patch("adibuild.core.toolchain.ArmToolchain.detect", return_value=None)
    mocker.patch("adibuild.core.toolchain.SystemToolchain.detect", return_value=system_info)

    result = cli_runner.invoke(cli, ["toolchain"])

    assert result.exit_code == 0
    assert "Vivado" in result.output
    assert "2023.2" in result.output
    assert "System" in result.output
    assert "11.4.0" in result.output
    # ARM should show as not found
    assert "not found" in result.output or "auto-download" in result.output
