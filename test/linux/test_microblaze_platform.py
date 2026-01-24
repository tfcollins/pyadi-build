"""Tests for MicroBlaze platform."""

import pytest

from adibuild.platforms.microblaze import MicroBlazePlatform


def test_microblaze_platform_init(microblaze_config_dict):
    """Test MicroBlaze platform initialization."""
    platform = MicroBlazePlatform(microblaze_config_dict)

    assert platform.arch == "microblaze"
    assert platform.cross_compile == "microblazeel-xilinx-linux-gnu-"
    assert platform.defconfig == "adi_mb_defconfig"
    assert platform.kernel_target == "simpleImage.vcu118_ad9081"


def test_microblaze_platform_invalid_arch():
    """Test error when arch is not 'microblaze'."""
    config = {
        "arch": "arm",  # Wrong arch for MicroBlaze
        "cross_compile": "microblazeel-xilinx-linux-gnu-",
        "defconfig": "adi_mb_defconfig",
        "kernel_target": "simpleImage.system",
    }

    with pytest.raises(ValueError, match="requires arch='microblaze'"):
        MicroBlazePlatform(config)


def test_microblaze_simpleimage_targets(microblaze_config_dict):
    """Test simpleImage targets property."""
    platform = MicroBlazePlatform(microblaze_config_dict)

    targets = platform.simpleimage_targets
    assert isinstance(targets, list)
    assert "simpleImage.vcu118_ad9081" in targets


def test_microblaze_simpleimage_targets_default():
    """Test simpleImage targets default to kernel_target."""
    config = {
        "arch": "microblaze",
        "cross_compile": "microblazeel-xilinx-linux-gnu-",
        "defconfig": "adi_mb_defconfig",
        "kernel_target": "simpleImage.system",
        "dtbs": [],
    }

    platform = MicroBlazePlatform(config)
    targets = platform.simpleimage_targets

    assert targets == ["simpleImage.system"]


def test_microblaze_simpleimage_targets_multiple():
    """Test multiple simpleImage targets."""
    config = {
        "arch": "microblaze",
        "cross_compile": "microblazeel-xilinx-linux-gnu-",
        "defconfig": "adi_mb_defconfig",
        "kernel_target": "simpleImage.system",
        "simpleimage_targets": [
            "simpleImage.system",
            "simpleImage.system_dts2",
        ],
        "dtbs": [],
    }

    platform = MicroBlazePlatform(config)
    targets = platform.simpleimage_targets

    assert len(targets) == 2
    assert "simpleImage.system" in targets
    assert "simpleImage.system_dts2" in targets


def test_microblaze_platform_get_make_env(microblaze_config_dict, mocker):
    """Test getting make environment variables with fallback to platform config."""
    from pathlib import Path

    from adibuild.core.toolchain import ToolchainInfo

    platform = MicroBlazePlatform(microblaze_config_dict)

    # Create a toolchain with MicroBlaze support
    toolchain_with_microblaze = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vivado/2023.2"),
        env_vars={"PATH": "/opt/Xilinx/Vivado/2023.2/bin"},
        cross_compile_arm32=None,
        cross_compile_arm64=None,
        cross_compile_microblaze="microblazeel-xilinx-linux-gnu-",
    )

    # Mock get_toolchain
    mocker.patch.object(platform, "get_toolchain", return_value=toolchain_with_microblaze)

    env = platform.get_make_env()

    assert env["ARCH"] == "microblaze"
    assert env["CROSS_COMPILE"] == "microblazeel-xilinx-linux-gnu-"
    assert "PATH" in env


def test_microblaze_platform_get_make_env_fallback(microblaze_config_dict, mocker):
    """Test getting make environment variables with fallback to platform config."""
    from pathlib import Path

    from adibuild.core.toolchain import ToolchainInfo

    platform = MicroBlazePlatform(microblaze_config_dict)

    # Create a toolchain without microblaze support to test fallback
    toolchain_without_microblaze = ToolchainInfo(
        type="mock",
        version="1.0.0",
        path=Path("/mock/toolchain"),
        env_vars={"PATH": "/mock/toolchain/bin"},
        cross_compile_arm32=None,
        cross_compile_arm64=None,
        cross_compile_microblaze=None,  # Test fallback
    )

    # Mock get_toolchain
    mocker.patch.object(platform, "get_toolchain", return_value=toolchain_without_microblaze)

    env = platform.get_make_env()

    assert env["ARCH"] == "microblaze"
    assert env["CROSS_COMPILE"] == "microblazeel-xilinx-linux-gnu-"  # Should use platform config


def test_microblaze_platform_dtb_path(microblaze_config_dict):
    """Test DTB path property."""
    platform = MicroBlazePlatform(microblaze_config_dict)
    assert platform.dtb_path == "arch/microblaze/boot/dts"


def test_microblaze_platform_kernel_image_path(microblaze_config_dict):
    """Test kernel image path property."""
    platform = MicroBlazePlatform(microblaze_config_dict)
    assert platform.kernel_image_path == "arch/microblaze/boot/simpleImage.vcu118_ad9081"


def test_microblaze_platform_dtbs(microblaze_config_dict):
    """Test DTB list is empty for MicroBlaze."""
    platform = MicroBlazePlatform(microblaze_config_dict)
    dtbs = platform.dtbs

    assert len(dtbs) == 0


def test_microblaze_platform_repr(microblaze_config_dict):
    """Test string representation."""
    platform = MicroBlazePlatform(microblaze_config_dict)
    repr_str = repr(platform)

    assert "MicroBlazePlatform" in repr_str
    assert "microblaze" in repr_str
    assert "simpleImage" in repr_str


def test_microblaze_default_dtb_path():
    """Test default DTB path."""
    config = {
        "arch": "microblaze",
        "cross_compile": "microblazeel-xilinx-linux-gnu-",
        "defconfig": "adi_mb_defconfig",
        "kernel_target": "simpleImage.system",
        "dtbs": [],
    }

    platform = MicroBlazePlatform(config)
    default_path = platform.get_default_dtb_path()

    assert default_path == "arch/microblaze/boot/dts"


def test_microblaze_default_kernel_image_path():
    """Test default kernel image path."""
    config = {
        "arch": "microblaze",
        "cross_compile": "microblazeel-xilinx-linux-gnu-",
        "defconfig": "adi_mb_defconfig",
        "kernel_target": "simpleImage.test",
        "dtbs": [],
    }

    platform = MicroBlazePlatform(config)
    default_path = platform.get_default_kernel_image_path()

    assert default_path == "arch/microblaze/boot/simpleImage.test"


def test_microblaze_kernel_target_warning(microblaze_config_dict, caplog):
    """Test warning for non-simpleImage kernel target."""
    config = microblaze_config_dict.copy()
    config["kernel_target"] = "zImage"  # Not a simpleImage target

    MicroBlazePlatform(config)

    # Check that warning was logged
    assert any("Unusual kernel target" in record.message for record in caplog.records)
