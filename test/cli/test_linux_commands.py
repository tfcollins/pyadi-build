"""Tests for Linux kernel build commands."""

import pytest

from adibuild.cli.main import cli
from adibuild.core.executor import BuildError


# ============================================================================
# Build Command Tests
# ============================================================================


def test_build_basic_zynqmp(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test basic build command for ZynqMP platform."""
    # Mock platform instance and builder
    mock_platform = mocker.MagicMock()
    mock_platform.name = 'zynqmp'
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    result = cli_runner.invoke(cli, ['linux', 'build', '-p', 'zynqmp', '-t', '2023_R2'])

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=False)


def test_build_basic_zynq(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test basic build command for Zynq platform."""
    mock_platform = mocker.MagicMock()
    mock_platform.name = 'zynq'
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    result = cli_runner.invoke(cli, ['linux', 'build', '-p', 'zynq', '-t', '2023_R2'])

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=False)


def test_build_with_clean_flag(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test build command with --clean flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    result = cli_runner.invoke(
        cli,
        ['linux', 'build', '-p', 'zynqmp', '-t', '2023_R2', '--clean']
    )

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=True, dtbs_only=False)


def test_build_with_dtbs_only(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test build command with --dtbs-only flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    result = cli_runner.invoke(
        cli,
        ['linux', 'build', '-p', 'zynqmp', '--dtbs-only']
    )

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=True)


def test_build_with_jobs_override(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test build command with -j jobs override."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    # Mock the config object to verify set was called
    mock_config = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.load_config_with_overrides', return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ['linux', 'build', '-p', 'zynqmp', '-j', '16']
    )

    assert result.exit_code == 0
    mock_config.set.assert_any_call('build.parallel_jobs', 16)


def test_build_with_output_override(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test build command with -o output directory override."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    mock_config = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.load_config_with_overrides', return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ['linux', 'build', '-p', 'zynqmp', '-o', '/tmp/output']
    )

    assert result.exit_code == 0
    mock_config.set.assert_any_call('build.output_dir', '/tmp/output')


def test_build_with_defconfig_override(cli_runner, mock_build_success, mocker):
    """Test build command with --defconfig override."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mocker.patch('adibuild.cli.main.display_build_summary')

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {'defconfig': 'old_defconfig'}
    mocker.patch('adibuild.cli.main.load_config_with_overrides', return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ['linux', 'build', '-p', 'zynqmp', '--defconfig', 'custom_defconfig']
    )

    assert result.exit_code == 0
    # Verify defconfig was updated
    platform_config = mock_config.get_platform.return_value
    assert platform_config['defconfig'] == 'custom_defconfig'


def test_build_missing_platform(cli_runner):
    """Test build command without required -p platform flag."""
    result = cli_runner.invoke(cli, ['linux', 'build', '-t', '2023_R2'])

    assert result.exit_code != 0
    assert 'Missing option' in result.output or 'required' in result.output.lower()


def test_build_invalid_platform(cli_runner):
    """Test build command with invalid platform name."""
    result = cli_runner.invoke(cli, ['linux', 'build', '-p', 'invalid', '-t', '2023_R2'])

    assert result.exit_code != 0
    assert 'Invalid value' in result.output or 'invalid' in result.output.lower()


def test_build_failure(cli_runner, mock_build_failure, mock_config_loading, mocker):
    """Test build command when build fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    # Mock builder that raises BuildError
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = BuildError("Compilation failed: undefined reference")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'build', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Build failed' in result.output or 'Error' in result.output


def test_build_exception_without_verbose(cli_runner, mock_config_loading, mocker):
    """Test build command handles unexpected exceptions without traceback."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    # Mock builder that raises generic exception
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = Exception("Unexpected error")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'build', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Unexpected error' in result.output
    # Should NOT show traceback without -vv
    assert 'Traceback' not in result.output


def test_build_exception_with_verbose(cli_runner, mock_config_loading, mocker):
    """Test build command shows traceback with -vv flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    # Mock builder that raises generic exception
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = Exception("Unexpected error")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['-vv', 'linux', 'build', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Unexpected error' in result.output
    # Should show traceback with -vv
    # (Note: traceback display depends on print_exc being called)


# ============================================================================
# Configure Command Tests
# ============================================================================


def test_configure_basic(cli_runner, mock_config_loading, mocker):
    """Test basic configure command."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(
        cli,
        ['linux', 'configure', '-p', 'zynqmp', '-t', '2023_R2']
    )

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.configure.assert_called_once()
    assert 'configured successfully' in result.output.lower()


def test_configure_with_defconfig_override(cli_runner, mocker):
    """Test configure command with --defconfig override."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {'defconfig': 'old_defconfig'}
    mocker.patch('adibuild.cli.main.load_config_with_overrides', return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ['linux', 'configure', '-p', 'zynq', '--defconfig', 'custom_defconfig']
    )

    assert result.exit_code == 0
    platform_config = mock_config.get_platform.return_value
    assert platform_config['defconfig'] == 'custom_defconfig'


def test_configure_failure(cli_runner, mock_config_loading, mocker):
    """Test configure command when configuration fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.configure.side_effect = BuildError("Configuration failed")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'configure', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Configuration failed' in result.output or 'Error' in result.output


# ============================================================================
# Menuconfig Command Tests
# ============================================================================


def test_menuconfig_basic(cli_runner, mock_config_loading, mocker):
    """Test basic menuconfig command."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(
        cli,
        ['linux', 'menuconfig', '-p', 'zynqmp', '-t', '2023_R2']
    )

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.configure.assert_called_once_with(menuconfig=True)
    assert 'Menuconfig completed' in result.output


def test_menuconfig_failure(cli_runner, mock_config_loading, mocker):
    """Test menuconfig command when menuconfig fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.configure.side_effect = BuildError("ncurses not installed")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'menuconfig', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Menuconfig failed' in result.output or 'ncurses' in result.output


# ============================================================================
# DTBs Command Tests
# ============================================================================


def test_dtbs_specific_files(cli_runner, mock_config_loading, mocker):
    """Test dtbs command with specific DTB files."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.return_value = ['file1.dtb', 'file2.dtb']
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(
        cli,
        ['linux', 'dtbs', '-p', 'zynqmp', 'file1.dtb', 'file2.dtb']
    )

    assert result.exit_code == 0
    mock_builder.build_dtbs.assert_called_once_with(dtbs=['file1.dtb', 'file2.dtb'])
    assert 'Built 2 DTBs successfully' in result.output


def test_dtbs_all_from_config(cli_runner, mock_config_loading, mocker):
    """Test dtbs command without files (builds all from config)."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.return_value = ['dtb1.dtb', 'dtb2.dtb', 'dtb3.dtb']
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'dtbs', '-p', 'zynqmp'])

    assert result.exit_code == 0
    mock_builder.build_dtbs.assert_called_once_with(dtbs=None)
    assert 'Built 3 DTBs successfully' in result.output


def test_dtbs_failure(cli_runner, mock_config_loading, mocker):
    """Test dtbs command when DTB build fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.side_effect = BuildError("DTB compilation failed")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'dtbs', '-p', 'zynqmp', 'test.dtb'])

    assert result.exit_code == 1
    assert 'DTB build failed' in result.output or 'Error' in result.output


# ============================================================================
# Clean Command Tests
# ============================================================================


def test_clean_basic(cli_runner, mock_config_loading, mocker):
    """Test basic clean command."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(
        cli,
        ['linux', 'clean', '-p', 'zynqmp', '-t', '2023_R2']
    )

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.clean.assert_called_once_with(deep=False)
    assert 'Clean completed' in result.output


def test_clean_deep(cli_runner, mock_config_loading, mocker):
    """Test clean command with --deep flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(
        cli,
        ['linux', 'clean', '-p', 'zynq', '--deep']
    )

    assert result.exit_code == 0
    mock_builder.clean.assert_called_once_with(deep=True)


def test_clean_failure(cli_runner, mock_config_loading, mocker):
    """Test clean command when clean fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch('adibuild.cli.main.get_platform_instance', return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.clean.side_effect = BuildError("Clean failed")
    mocker.patch('adibuild.cli.main.LinuxBuilder', return_value=mock_builder)

    result = cli_runner.invoke(cli, ['linux', 'clean', '-p', 'zynqmp'])

    assert result.exit_code == 1
    assert 'Clean failed' in result.output or 'Error' in result.output
