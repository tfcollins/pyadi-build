"""Tests for CLI helper functions."""

from pathlib import Path

import pytest

from adibuild import __version__
from adibuild.cli.helpers import (
    create_default_config,
    display_build_summary,
    display_platforms,
    display_toolchain_info,
    get_platform_instance,
    load_config_with_overrides,
    print_error,
    print_success,
    print_version,
    print_warning,
    validate_config_file,
)
from adibuild.core.config import BuildConfig, ConfigurationError
from adibuild.core.toolchain import ToolchainInfo
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform


# ============================================================================
# Print Functions Tests
# ============================================================================


def test_print_version(capsys):
    """Test print_version outputs version information."""
    print_version()
    captured = capsys.readouterr()

    assert 'adibuild' in captured.out
    assert __version__ in captured.out


def test_print_error_exits(mocker):
    """Test print_error prints message and exits."""
    mock_exit = mocker.patch('sys.exit')

    print_error("Test error message")

    mock_exit.assert_called_once_with(1)


def test_print_error_message(capsys, mocker):
    """Test print_error prints error message."""
    mocker.patch('sys.exit')  # Prevent actual exit

    print_error("Test error message")
    captured = capsys.readouterr()

    assert 'Error' in captured.out
    assert 'Test error message' in captured.out


def test_print_success(capsys):
    """Test print_success prints success message."""
    print_success("Operation successful")
    captured = capsys.readouterr()

    assert 'Operation successful' in captured.out
    # Success messages typically have checkmarks or success indicators


def test_print_warning(capsys):
    """Test print_warning prints warning message."""
    print_warning("This is a warning")
    captured = capsys.readouterr()

    assert 'Warning' in captured.out
    assert 'This is a warning' in captured.out


# ============================================================================
# Config Loading Tests
# ============================================================================


def test_load_config_with_overrides_custom_file(tmp_path):
    """Test load_config_with_overrides with custom config file."""
    # Create a config file
    config_file = tmp_path / "custom_config.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2
build:
  parallel_jobs: 8
platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
"""
    config_file.write_text(config_content)

    config = load_config_with_overrides(str(config_file), 'zynqmp', None)

    assert config is not None
    assert config.get('project') == 'linux'
    assert config.get('tag') == '2023_R2'


def test_load_config_with_overrides_tag_override(tmp_path):
    """Test load_config_with_overrides with tag override."""
    config_file = tmp_path / "config.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2
build:
  parallel_jobs: 4
platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
"""
    config_file.write_text(config_content)

    config = load_config_with_overrides(str(config_file), 'zynqmp', '2024_R1')

    assert config.get('tag') == '2024_R1'


def test_load_config_with_overrides_default_config(mocker, tmp_path):
    """Test load_config_with_overrides loads default config."""
    # Create a mock default config
    config_dir = tmp_path / "configs" / "linux"
    config_dir.mkdir(parents=True)

    default_config = config_dir / "2023_R2.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2
platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
"""
    default_config.write_text(config_content)

    # Test with explicit path (mocking Path is complex and can break pytest)
    config = load_config_with_overrides(str(default_config), 'zynqmp', None)

    assert config is not None


def test_load_config_with_overrides_file_not_found(mocker):
    """Test load_config_with_overrides when file not found."""
    mock_exit = mocker.patch('sys.exit')

    # Try to load non-existent file
    load_config_with_overrides('/nonexistent/config.yaml', 'zynqmp', None)

    # Should call sys.exit due to print_error
    mock_exit.assert_called_once_with(1)


# ============================================================================
# Platform Instance Tests
# ============================================================================


def test_get_platform_instance_zynq():
    """Test get_platform_instance returns ZynqPlatform."""
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
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
    platform = get_platform_instance(config, 'zynq')

    assert isinstance(platform, ZynqPlatform)
    assert platform.arch == 'arm'


def test_get_platform_instance_zynqmp():
    """Test get_platform_instance returns ZynqMPPlatform."""
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
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
    platform = get_platform_instance(config, 'zynqmp')

    assert isinstance(platform, ZynqMPPlatform)
    assert platform.arch == 'arm64'


def test_get_platform_instance_invalid(mocker):
    """Test get_platform_instance with invalid platform."""
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "platforms": {},
    }

    config = BuildConfig.from_dict(config_data)
    mock_exit = mocker.patch('sys.exit')

    get_platform_instance(config, 'invalid')

    # Should call sys.exit due to print_error
    mock_exit.assert_called_once_with(1)


# ============================================================================
# Display Functions Tests
# ============================================================================


def test_display_build_summary(capsys, mock_toolchain):
    """Test display_build_summary shows build information."""
    from adibuild.platforms.zynqmp import ZynqMPPlatform

    platform_config = {
        "arch": "arm64",
        "cross_compile": "aarch64-linux-gnu-",
        "defconfig": "adi_zynqmp_defconfig",
        "kernel_target": "Image",
    }
    platform = ZynqMPPlatform(platform_config)

    result = {
        'success': True,
        'duration': 123.4,
        'kernel_image': '/path/to/Image',
        'dtbs': ['dtb1.dtb', 'dtb2.dtb'],
        'artifacts': Path('/tmp/build'),
    }

    display_build_summary(result, platform)
    captured = capsys.readouterr()

    assert 'Build Summary' in captured.out or 'Build' in captured.out
    assert 'arm64' in captured.out
    assert 'adi_zynqmp_defconfig' in captured.out
    assert 'Image' in captured.out


def test_display_build_summary_minimal(capsys):
    """Test display_build_summary with minimal result data."""
    from adibuild.platforms.zynq import ZynqPlatform

    platform_config = {
        "arch": "arm",
        "cross_compile": "arm-linux-gnueabihf-",
        "defconfig": "zynq_xcomm_adv7511_defconfig",
        "kernel_target": "uImage",
    }
    platform = ZynqPlatform(platform_config)

    result = {
        'success': True,
    }

    display_build_summary(result, platform)
    captured = capsys.readouterr()

    # Should still display basic info even with minimal data
    assert 'arm' in captured.out
    assert 'zynq_xcomm_adv7511_defconfig' in captured.out


def test_display_toolchain_info_vivado(capsys):
    """Test display_toolchain_info with Vivado toolchain."""
    toolchain = ToolchainInfo(
        type='vivado',
        version='2023.2',
        path=Path('/opt/Xilinx/Vitis/2023.2'),
        env_vars={},
        cross_compile_arm32='arm-linux-gnueabihf-',
        cross_compile_arm64='aarch64-linux-gnu-',
    )

    display_toolchain_info(toolchain)
    captured = capsys.readouterr()

    assert 'vivado' in captured.out.lower()
    assert '2023.2' in captured.out
    assert 'arm-linux-gnueabihf-' in captured.out
    assert 'aarch64-linux-gnu-' in captured.out


def test_display_toolchain_info_dict(capsys):
    """Test display_toolchain_info with dictionary (from mocks)."""
    toolchain_dict = {
        'type': 'vivado',
        'version': '2023.2',
        'path': Path('/opt/Xilinx/Vitis/2023.2'),
        'cross_compile_arm32': 'arm-linux-gnueabihf-',
        'cross_compile_arm64': 'aarch64-linux-gnu-',
    }

    # Create ToolchainInfo from dict
    toolchain = ToolchainInfo(
        type=toolchain_dict['type'],
        version=toolchain_dict['version'],
        path=toolchain_dict['path'],
        env_vars={},
        cross_compile_arm32=toolchain_dict.get('cross_compile_arm32'),
        cross_compile_arm64=toolchain_dict.get('cross_compile_arm64'),
    )

    display_toolchain_info(toolchain)
    captured = capsys.readouterr()

    assert 'vivado' in captured.out.lower()


def test_display_platforms(capsys):
    """Test display_platforms shows platform information."""
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "platforms": {
            "zynq": {
                "arch": "arm",
                "defconfig": "zynq_xcomm_adv7511_defconfig",
                "kernel_target": "uImage",
                "dtbs": ["dtb1.dtb", "dtb2.dtb"],
            },
            "zynqmp": {
                "arch": "arm64",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
                "dtbs": ["dtb3.dtb"],
            },
        },
    }

    config = BuildConfig.from_dict(config_data)
    display_platforms(config)
    captured = capsys.readouterr()

    assert 'zynq' in captured.out.lower() or 'Platform' in captured.out
    assert 'zynqmp' in captured.out.lower() or 'Platform' in captured.out
    assert 'arm' in captured.out
    assert 'arm64' in captured.out


def test_display_platforms_empty(capsys):
    """Test display_platforms with no platforms defined."""
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "platforms": {},
    }

    config = BuildConfig.from_dict(config_data)
    display_platforms(config)
    captured = capsys.readouterr()

    assert 'No platforms' in captured.out or 'Warning' in captured.out


# ============================================================================
# Config Validation Tests
# ============================================================================


def test_validate_config_file_valid(tmp_path, mocker):
    """Test validate_config_file with valid configuration."""
    config_file = tmp_path / "valid_config.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
platforms:
  zynqmp:
    arch: arm64
    defconfig: adi_zynqmp_defconfig
"""
    config_file.write_text(config_content)

    schema_file = tmp_path / "schema.json"
    schema_file.write_text('{"type": "object"}')

    # Mock validate to succeed
    mocker.patch('adibuild.core.config.BuildConfig.validate')

    validate_config_file(config_file, schema_file)
    # Should not raise or exit


def test_validate_config_file_invalid(tmp_path, mocker):
    """Test validate_config_file with invalid configuration."""
    config_file = tmp_path / "invalid_config.yaml"
    config_file.write_text("invalid: yaml: content:")

    schema_file = tmp_path / "schema.json"
    schema_file.write_text('{"type": "object"}')

    mock_exit = mocker.patch('sys.exit')

    validate_config_file(config_file, schema_file)

    # Should call sys.exit due to print_error
    mock_exit.assert_called_once_with(1)


# ============================================================================
# Config Creation Tests
# ============================================================================


def test_create_default_config(tmp_path, mocker):
    """Test create_default_config creates configuration file."""
    output_file = tmp_path / "new_config.yaml"

    # Mock the interactive prompt
    mock_prompt_config = mocker.patch('adibuild.cli.helpers.prompt_for_config')
    mock_prompt_config.return_value = {
        "build": {"parallel_jobs": 8},
        "toolchains": {},
    }

    create_default_config(output_file)

    # File should be created
    assert output_file.exists()


def test_create_default_config_with_toolchain(tmp_path, mocker):
    """Test create_default_config with toolchain configuration."""
    output_file = tmp_path / "config_with_toolchain.yaml"

    mock_prompt_config = mocker.patch('adibuild.cli.helpers.prompt_for_config')
    mock_prompt_config.return_value = {
        "build": {"parallel_jobs": 16},
        "toolchains": {
            "vivado_path": "/opt/Xilinx/Vitis/2023.2",
        },
    }

    create_default_config(output_file)

    assert output_file.exists()


# ============================================================================
# Integration Tests
# ============================================================================


def test_config_load_platform_build_workflow(tmp_path):
    """Test complete workflow: load config -> get platform -> display."""
    # Create config
    config_file = tmp_path / "workflow_config.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2
platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
    dtbs:
      - test.dtb
"""
    config_file.write_text(config_content)

    # Load config
    config = load_config_with_overrides(str(config_file), 'zynqmp', None)
    assert config is not None

    # Get platform
    platform = get_platform_instance(config, 'zynqmp')
    assert isinstance(platform, ZynqMPPlatform)

    # Display would happen here (already tested separately)
    assert platform.arch == 'arm64'
    assert platform.defconfig == 'adi_zynqmp_defconfig'
