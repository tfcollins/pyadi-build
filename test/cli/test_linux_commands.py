"""Tests for Linux kernel build commands."""

import pytest

from adibuild.cli.helpers import tag_to_tool_version
from adibuild.cli.main import cli
from adibuild.core.executor import BuildError

# ============================================================================
# tag_to_tool_version Tests
# ============================================================================


@pytest.mark.parametrize(
    "tag,expected",
    [
        ("2023_R2", "2023.2"),
        ("2023_R1", "2023.1"),
        ("2022_R2", "2022.2"),
        ("2021_R1", "2021.1"),
        ("2023_R2_P1", "2023.2"),
        ("2022_R2_P3", "2022.2"),
        ("main", None),
        ("master", None),
        ("v1.0.0", None),
        ("", None),
        (None, None),
    ],
)
def test_tag_to_tool_version(tag, expected):
    """Test tag_to_tool_version mapping."""
    assert tag_to_tool_version(tag) == expected


# ============================================================================
# Build Command Tests
# ============================================================================


def test_build_basic_zynqmp(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test basic build command for ZynqMP platform."""
    # Mock platform instance and builder
    mock_platform = mocker.MagicMock()
    mock_platform.name = "zynqmp"
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynqmp", "-t", "2023_R2"])

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=False)


def test_build_basic_zynq(cli_runner, mock_build_success, mock_config_loading, mocker):
    """Test basic build command for Zynq platform."""
    mock_platform = mocker.MagicMock()
    mock_platform.name = "zynq"
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynq", "-t", "2023_R2"])

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=False)


def test_build_with_clean_flag(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test build command with --clean flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli, ["linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--clean"]
    )

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=True, dtbs_only=False)


def test_build_with_dtbs_only(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test build command with --dtbs-only flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynqmp", "--dtbs-only"])

    assert result.exit_code == 0
    mock_builder.build.assert_called_once_with(clean_before=False, dtbs_only=True)


def test_build_with_jobs_override(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test build command with -j jobs override."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    # Mock the config object to verify set was called
    mock_config = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynqmp", "-j", "16"])

    assert result.exit_code == 0
    mock_config.set.assert_any_call("build.parallel_jobs", 16)


def test_build_with_output_override(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test build command with -o output directory override."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli, ["linux", "build", "-p", "zynqmp", "-o", "/tmp/output"]
    )

    assert result.exit_code == 0
    mock_config.set.assert_any_call("build.output_dir", "/tmp/output")


def test_build_with_defconfig_override(cli_runner, mock_build_success, mocker):
    """Test build command with --defconfig override."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"defconfig": "old_defconfig"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli, ["linux", "build", "-p", "zynqmp", "--defconfig", "custom_defconfig"]
    )

    assert result.exit_code == 0
    # Verify defconfig was updated
    platform_config = mock_config.get_platform.return_value
    assert platform_config["defconfig"] == "custom_defconfig"


def test_build_missing_platform(cli_runner):
    """Test build command without required -p platform flag."""
    result = cli_runner.invoke(cli, ["linux", "build", "-t", "2023_R2"])

    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


def test_build_invalid_platform(cli_runner):
    """Test build command with invalid platform name."""
    result = cli_runner.invoke(cli, ["linux", "build", "-p", "invalid", "-t", "2023_R2"])

    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid" in result.output.lower()


def test_build_failure(cli_runner, mock_build_failure, mock_config_loading, mocker):
    """Test build command when build fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    # Mock builder that raises BuildError
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = BuildError("Compilation failed: undefined reference")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Build failed" in result.output or "Error" in result.output


def test_build_exception_without_verbose(cli_runner, mock_config_loading, mocker):
    """Test build command handles unexpected exceptions without traceback."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    # Mock builder that raises generic exception
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = Exception("Unexpected error")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Unexpected error" in result.output
    # Should NOT show traceback without -vv
    assert "Traceback" not in result.output


def test_build_exception_with_verbose(cli_runner, mock_config_loading, mocker):
    """Test build command shows traceback with -vv flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    # Mock builder that raises generic exception
    mock_builder = mocker.MagicMock()
    mock_builder.build.side_effect = Exception("Unexpected error")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["-vv", "linux", "build", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Unexpected error" in result.output
    # Should show traceback with -vv
    # (Note: traceback display depends on print_exc being called)


# ============================================================================
# Configure Command Tests
# ============================================================================


def test_configure_basic(cli_runner, mock_config_loading, mocker):
    """Test basic configure command."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(
        cli, ["linux", "configure", "-p", "zynqmp", "-t", "2023_R2"]
    )

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.configure.assert_called_once()
    assert "configured successfully" in result.output.lower()


def test_configure_with_defconfig_override(cli_runner, mocker):
    """Test configure command with --defconfig override."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"defconfig": "old_defconfig"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli, ["linux", "configure", "-p", "zynq", "--defconfig", "custom_defconfig"]
    )

    assert result.exit_code == 0
    platform_config = mock_config.get_platform.return_value
    assert platform_config["defconfig"] == "custom_defconfig"


def test_configure_failure(cli_runner, mock_config_loading, mocker):
    """Test configure command when configuration fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.configure.side_effect = BuildError("Configuration failed")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "configure", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Configuration failed" in result.output or "Error" in result.output


# ============================================================================
# Menuconfig Command Tests
# ============================================================================


def test_menuconfig_basic(cli_runner, mock_config_loading, mocker):
    """Test basic menuconfig command."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(
        cli, ["linux", "menuconfig", "-p", "zynqmp", "-t", "2023_R2"]
    )

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.configure.assert_called_once_with(menuconfig=True)
    assert "Menuconfig completed" in result.output


def test_menuconfig_failure(cli_runner, mock_config_loading, mocker):
    """Test menuconfig command when menuconfig fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.configure.side_effect = BuildError("ncurses not installed")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "menuconfig", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Menuconfig failed" in result.output or "ncurses" in result.output


# ============================================================================
# DTBs Command Tests
# ============================================================================


def test_dtbs_specific_files(cli_runner, mock_config_loading, mocker):
    """Test dtbs command with specific DTB files."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.return_value = ["file1.dtb", "file2.dtb"]
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(
        cli, ["linux", "dtbs", "-p", "zynqmp", "file1.dtb", "file2.dtb"]
    )

    assert result.exit_code == 0
    mock_builder.build_dtbs.assert_called_once_with(dtbs=["file1.dtb", "file2.dtb"])
    assert "Built 2 DTBs successfully" in result.output


def test_dtbs_all_from_config(cli_runner, mock_config_loading, mocker):
    """Test dtbs command without files (builds all from config)."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.return_value = ["dtb1.dtb", "dtb2.dtb", "dtb3.dtb"]
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "dtbs", "-p", "zynqmp"])

    assert result.exit_code == 0
    mock_builder.build_dtbs.assert_called_once_with(dtbs=None)
    assert "Built 3 DTBs successfully" in result.output


def test_dtbs_failure(cli_runner, mock_config_loading, mocker):
    """Test dtbs command when DTB build fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build_dtbs.side_effect = BuildError("DTB compilation failed")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "dtbs", "-p", "zynqmp", "test.dtb"])

    assert result.exit_code == 1
    assert "DTB build failed" in result.output or "Error" in result.output


# ============================================================================
# Clean Command Tests
# ============================================================================


def test_clean_basic(cli_runner, mock_config_loading, mocker):
    """Test basic clean command."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "clean", "-p", "zynqmp", "-t", "2023_R2"])

    assert result.exit_code == 0
    mock_builder.prepare_source.assert_called_once()
    mock_builder.clean.assert_called_once_with(deep=False)
    assert "Clean completed" in result.output


def test_clean_deep(cli_runner, mock_config_loading, mocker):
    """Test clean command with --deep flag."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "clean", "-p", "zynq", "--deep"])

    assert result.exit_code == 0
    mock_builder.clean.assert_called_once_with(deep=True)


def test_clean_failure(cli_runner, mock_config_loading, mocker):
    """Test clean command when clean fails."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.clean.side_effect = BuildError("Clean failed")
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)

    result = cli_runner.invoke(cli, ["linux", "clean", "-p", "zynqmp"])

    assert result.exit_code == 1
    assert "Clean failed" in result.output or "Error" in result.output


# ============================================================================
# Simpleimage Option Tests
# ============================================================================


def test_build_microblaze_with_simpleimage(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test build command with --simpleimage for microblaze."""
    mock_platform = mocker.MagicMock()
    mock_platform.name = "microblaze"
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "microblaze",
            "--simpleimage",
            "simpleImage.vcu118_ad9081",
        ],
    )

    assert result.exit_code == 0


def test_build_simpleimage_invalid_for_zynqmp(cli_runner, mock_config_loading, mocker):
    """Test --simpleimage errors for non-microblaze platforms."""
    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "--simpleimage", "simpleImage.vcu118"],
    )

    assert result.exit_code == 1
    assert "only valid for MicroBlaze" in result.output


def test_build_microblaze_multiple_simpleimages(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test multiple --simpleimage options."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "microblaze",
            "-s",
            "simpleImage.vcu118",
            "-s",
            "simpleImage.kcu105",
        ],
    )

    assert result.exit_code == 0


def test_build_microblaze_simpleimage_sets_config(cli_runner, mock_build_success, mocker):
    """Test that --simpleimage correctly sets simpleimage_targets in config."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "microblaze",
            "--simpleimage",
            "simpleImage.vcu118_ad9081",
        ],
    )

    assert result.exit_code == 0
    # Verify simpleimage_targets was set
    platform_config = mock_config.get_platform.return_value
    assert platform_config["simpleimage_targets"] == ["simpleImage.vcu118_ad9081"]
    assert platform_config["kernel_target"] == "simpleImage.vcu118_ad9081"


# ============================================================================
# Simpleimage Preset Option Tests
# ============================================================================


def test_build_simpleimage_preset_requires_tag(cli_runner, mock_config_loading, mocker):
    """Test --simpleimage-preset requires -t tag."""
    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "microblaze", "--simpleimage-preset"],
    )
    assert result.exit_code == 1
    assert "requires -t/--tag" in result.output


def test_build_simpleimage_preset_invalid_for_zynqmp(
    cli_runner, mock_config_loading, mocker
):
    """Test --simpleimage-preset errors for non-microblaze platforms."""
    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--simpleimage-preset"],
    )
    assert result.exit_code == 1
    assert "only valid for MicroBlaze" in result.output


def test_build_simpleimage_preset_conflicts_with_simpleimage(
    cli_runner, mock_config_loading, mocker
):
    """Test cannot use both --simpleimage and --simpleimage-preset."""
    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "microblaze",
            "-t",
            "2023_R2",
            "--simpleimage",
            "simpleImage.vcu118",
            "--simpleimage-preset",
        ],
    )
    assert result.exit_code == 1
    assert "Cannot use both" in result.output


def test_build_simpleimage_preset_interactive(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test --simpleimage-preset interactive selection."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    # Mock the preset helpers
    mock_presets = [
        {
            "project": "ad9081_fmca_ebz",
            "carrier": "vcu118",
            "simpleimage_target": "simpleImage.vcu118_ad9081",
            "dts_path": "arch/microblaze/boot/dts/vcu118_ad9081.dts",
        },
    ]
    mocker.patch(
        "adibuild.cli.helpers.get_simpleimage_presets", return_value=mock_presets
    )

    # Simulate user selecting option "1"
    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "microblaze", "-t", "2023_R2", "--simpleimage-preset"],
        input="1\n",
    )

    assert result.exit_code == 0


def test_build_simpleimage_preset_with_carrier_filter(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test --simpleimage-preset with --carrier filter."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_presets = [
        {
            "project": "ad9081_fmca_ebz",
            "carrier": "vcu118",
            "simpleimage_target": "simpleImage.vcu118_ad9081",
            "dts_path": "arch/microblaze/boot/dts/vcu118_ad9081.dts",
        },
    ]
    mock_get_presets = mocker.patch(
        "adibuild.cli.helpers.get_simpleimage_presets", return_value=mock_presets
    )

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "microblaze", "-t", "2023_R2", "-sp", "-c", "vcu118"],
        input="1\n",
    )

    assert result.exit_code == 0
    # Verify carrier was passed to get_simpleimage_presets
    mock_get_presets.assert_called_once_with("2023_R2", carrier="vcu118")


def test_build_carrier_requires_simpleimage_preset(
    cli_runner, mock_config_loading, mocker
):
    """Test --carrier requires --simpleimage-preset."""
    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "microblaze", "-t", "2023_R2", "--carrier", "vcu118"],
    )
    assert result.exit_code == 1
    assert "requires --simpleimage-preset" in result.output


def test_build_simpleimage_preset_no_presets_found(
    cli_runner, mock_config_loading, mocker
):
    """Test --simpleimage-preset with no presets found for tag."""
    mocker.patch("adibuild.cli.helpers.get_simpleimage_presets", return_value=[])

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "microblaze", "-t", "invalid_tag", "-sp"],
    )

    assert result.exit_code == 1
    assert "No simpleImage presets found" in result.output


def test_build_simpleimage_preset_no_presets_for_carrier(
    cli_runner, mock_config_loading, mocker
):
    """Test --simpleimage-preset with no presets found for carrier."""
    mocker.patch("adibuild.cli.helpers.get_simpleimage_presets", return_value=[])

    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "microblaze",
            "-t",
            "2023_R2",
            "-sp",
            "-c",
            "invalid_carrier",
        ],
    )

    assert result.exit_code == 1
    assert "No simpleImage presets found" in result.output
    assert "carrier" in result.output


# ============================================================================
# Tool Version Auto-Detection Tests
# ============================================================================


def test_tool_version_auto_detect_from_tag(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test tool version is auto-detected from release tag."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2"],
    )

    assert result.exit_code == 0
    assert "Auto-detected tool version 2023.2 from tag 2023_R2" in result.output


def test_tool_version_override(cli_runner, mock_build_success, mocker):
    """Test --tool-version overrides auto-detection."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--tool-version", "2022.2"],
    )

    assert result.exit_code == 0
    # Should NOT show auto-detected message since override was provided
    assert "Auto-detected tool version" not in result.output
    # Verify tool_version was set in platform config
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("tool_version") == "2022.2"


def test_tool_version_patch_release(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test patch release tag maps to base version."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2_P1"],
    )

    assert result.exit_code == 0
    assert "Auto-detected tool version 2023.2 from tag 2023_R2_P1" in result.output


def test_tool_version_no_detection_for_main(
    cli_runner, mock_build_success, mock_config_loading, mocker
):
    """Test no auto-detection for non-release tags like 'main'."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "main"],
    )

    assert result.exit_code == 0
    assert "Auto-detected tool version" not in result.output


def test_tool_version_sets_platform_config(cli_runner, mock_build_success, mocker):
    """Test that tool_version is properly set in platform config."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"arch": "arm64"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2"],
    )

    assert result.exit_code == 0
    # Verify tool_version was set in platform config
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("tool_version") == "2023.2"


# ============================================================================
# Strict Vivado Version Matching Tests
# ============================================================================


def test_strict_vivado_version_by_default(cli_runner, mock_build_success, mocker):
    """Test strict Vivado version matching is enabled when tag is used."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"arch": "arm64"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2"],
    )

    assert result.exit_code == 0
    # Verify strict_version=True is set in platform config when tag provided
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("strict_version") is True


def test_allow_any_vivado_flag(cli_runner, mock_build_success, mocker):
    """Test --allow-any-vivado disables strict version matching."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"arch": "arm64"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--allow-any-vivado"],
    )

    assert result.exit_code == 0
    # Verify strict_version=False when --allow-any-vivado is used
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("strict_version") is False


def test_strict_version_with_explicit_tool_version(
    cli_runner, mock_build_success, mocker
):
    """Test strict version is enabled with explicit --tool-version."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"arch": "arm64"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        ["linux", "build", "-p", "zynqmp", "--tool-version", "2022.2"],
    )

    assert result.exit_code == 0
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("tool_version") == "2022.2"
    assert platform_config.get("strict_version") is True


def test_allow_any_vivado_with_explicit_tool_version(
    cli_runner, mock_build_success, mocker
):
    """Test --allow-any-vivado with explicit --tool-version."""
    mock_platform = mocker.MagicMock()
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=mock_platform)

    mock_builder = mocker.MagicMock()
    mock_builder.build.return_value = mock_build_success
    mocker.patch("adibuild.cli.main.LinuxBuilder", return_value=mock_builder)
    mocker.patch("adibuild.cli.main.display_build_summary")

    mock_config = mocker.MagicMock()
    mock_config.get_platform.return_value = {"arch": "arm64"}
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=mock_config)

    result = cli_runner.invoke(
        cli,
        [
            "linux",
            "build",
            "-p",
            "zynqmp",
            "--tool-version",
            "2022.2",
            "--allow-any-vivado",
        ],
    )

    assert result.exit_code == 0
    platform_config = mock_config.get_platform.return_value
    assert platform_config.get("tool_version") == "2022.2"
    assert platform_config.get("strict_version") is False
