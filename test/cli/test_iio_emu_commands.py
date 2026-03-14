"""Tests for iio-emu and libtinyiiod CLI commands."""

import pytest
from adibuild.cli.main import cli
from adibuild.core.config import BuildConfig


def test_libtinyiiod_help(cli_runner):
    """Test libtinyiiod command group shows help."""
    result = cli_runner.invoke(cli, ["libtinyiiod", "--help"])

    assert result.exit_code == 0
    assert "libtinyiiod library build commands" in result.output
    assert "build" in result.output
    assert "clean" in result.output


def test_iio_emu_help(cli_runner):
    """Test iio-emu command group shows help."""
    result = cli_runner.invoke(cli, ["iio-emu", "--help"])

    assert result.exit_code == 0
    assert "iio-emu server application build commands" in result.output
    assert "build" in result.output
    assert "clean" in result.output


def test_iio_oscilloscope_help(cli_runner):
    """Test iio-oscilloscope command group shows help."""
    result = cli_runner.invoke(cli, ["osc", "--help"])

    assert result.exit_code == 0
    assert "iio-oscilloscope GUI application build commands" in result.output
    assert "build" in result.output
    assert "clean" in result.output


def test_build_libtinyiiod_mock(cli_runner, mocker, tmp_path):
    """Test building libtinyiiod with mocked builder."""
    mock_load_config = mocker.patch("adibuild.cli.main.load_config_with_overrides")
    mock_get_platform = mocker.patch("adibuild.cli.main.get_platform_instance")
    mock_builder = mocker.patch("adibuild.cli.main.LibTinyIIODBuilder")

    # Setup mock returns
    mock_config = BuildConfig.from_dict({
        "project": "libtinyiiod",
        "tag": "main",
        "platforms": {
            "native": {"arch": "native"}
        }
    })
    mock_load_config.return_value = mock_config
    
    mock_platform = mocker.MagicMock()
    mock_platform.arch = "native"
    mock_get_platform.return_value = mock_platform

    mock_builder_instance = mocker.MagicMock()
    mock_builder.return_value = mock_builder_instance
    mock_builder_instance.build.return_value = {
        "artifacts": ["libtinyiiod.so"],
        "output_dir": "/tmp/build"
    }

    result = cli_runner.invoke(cli, ["libtinyiiod", "build", "-p", "native"])

    assert result.exit_code == 0
    assert "libtinyiiod built successfully" in result.output
    mock_builder.assert_called_once()


def test_build_iio_emu_mock(cli_runner, mocker, tmp_path):
    """Test building iio-emu with mocked builder."""
    mock_load_config = mocker.patch("adibuild.cli.main.load_config_with_overrides")
    mock_get_platform = mocker.patch("adibuild.cli.main.get_platform_instance")
    mock_builder = mocker.patch("adibuild.cli.main.IIOEmuBuilder")

    # Setup mock returns
    mock_config = BuildConfig.from_dict({
        "project": "iio-emu",
        "tag": "main",
        "platforms": {
            "native": {"arch": "native"}
        }
    })
    mock_load_config.return_value = mock_config
    
    mock_platform = mocker.MagicMock()
    mock_platform.arch = "native"
    mock_get_platform.return_value = mock_platform

    mock_builder_instance = mocker.MagicMock()
    mock_builder.return_value = mock_builder_instance
    mock_builder_instance.build.return_value = {
        "artifacts": ["iio-emu"],
        "output_dir": "/tmp/build"
    }

    result = cli_runner.invoke(cli, ["iio-emu", "build", "-p", "native"])

    assert result.exit_code == 0
    assert "iio-emu built successfully" in result.output
    mock_builder.assert_called_once()


def test_build_iio_oscilloscope_mock(cli_runner, mocker, tmp_path):
    """Test building iio-oscilloscope with mocked builder."""
    mock_load_config = mocker.patch("adibuild.cli.main.load_config_with_overrides")
    mock_get_platform = mocker.patch("adibuild.cli.main.get_platform_instance")
    mock_builder = mocker.patch("adibuild.cli.main.IIOOscilloscopeBuilder")

    # Setup mock returns
    mock_config = BuildConfig.from_dict({
        "project": "iio-oscilloscope",
        "tag": "main",
        "platforms": {
            "native": {"arch": "native"}
        }
    })
    mock_load_config.return_value = mock_config
    
    mock_platform = mocker.MagicMock()
    mock_platform.arch = "native"
    mock_get_platform.return_value = mock_platform

    mock_builder_instance = mocker.MagicMock()
    mock_builder.return_value = mock_builder_instance
    mock_builder_instance.build.return_value = {
        "artifacts": ["iio-oscilloscope"],
        "output_dir": "/tmp/build"
    }

    result = cli_runner.invoke(cli, ["osc", "build", "-p", "native"])

    assert result.exit_code == 0
    assert "iio-oscilloscope built successfully" in result.output
    mock_builder.assert_called_once()
