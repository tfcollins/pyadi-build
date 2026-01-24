"""Tests for Zynq platform."""

import pytest

from adibuild.platforms.zynq import ZynqPlatform


def test_zynq_platform_init(zynq_config_dict):
    """Test Zynq platform initialization."""
    platform = ZynqPlatform(zynq_config_dict)

    assert platform.arch == "arm"
    assert platform.cross_compile == "arm-linux-gnueabihf-"
    assert platform.defconfig == "zynq_xcomm_adv7511_defconfig"
    assert platform.kernel_target == "uImage"


def test_zynq_platform_invalid_arch():
    """Test error when arch is not 'arm'."""
    config = {
        "arch": "arm64",  # Wrong arch for Zynq
        "cross_compile": "arm-linux-gnueabihf-",
        "defconfig": "test_defconfig",
        "kernel_target": "uImage",
    }

    with pytest.raises(ValueError, match="requires arch='arm'"):
        ZynqPlatform(config)


def test_zynq_platform_get_make_env(zynq_config_dict, mocker):
    """Test getting make environment variables with fallback to platform config."""
    from pathlib import Path

    from adibuild.core.toolchain import ToolchainInfo

    platform = ZynqPlatform(zynq_config_dict)

    # Create a toolchain without cross_compile values to test fallback behavior
    toolchain_without_cross_compile = ToolchainInfo(
        type="mock",
        version="1.0.0",
        path=Path("/mock/toolchain"),
        env_vars={"PATH": "/mock/toolchain/bin"},
        cross_compile_arm32=None,  # Test fallback to platform config
        cross_compile_arm64=None,
    )

    # Mock get_toolchain
    mocker.patch.object(platform, "get_toolchain", return_value=toolchain_without_cross_compile)

    env = platform.get_make_env()

    assert env["ARCH"] == "arm"
    assert env["CROSS_COMPILE"] == "arm-linux-gnueabihf-"  # Should use platform config
    assert env["LOADADDR"] == "0x8000"  # Zynq uses LOADADDR, not UIMAGE_LOADADDR
    assert "PATH" in env


def test_zynq_platform_dtb_path(zynq_config_dict):
    """Test DTB path property."""
    platform = ZynqPlatform(zynq_config_dict)
    assert platform.dtb_path == "arch/arm/boot/dts"


def test_zynq_platform_kernel_image_path(zynq_config_dict):
    """Test kernel image path property."""
    platform = ZynqPlatform(zynq_config_dict)
    assert platform.kernel_image_path == "arch/arm/boot/uImage"


def test_zynq_platform_dtbs(zynq_config_dict):
    """Test DTB list property."""
    platform = ZynqPlatform(zynq_config_dict)
    dtbs = platform.dtbs

    assert len(dtbs) == 2
    assert "zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb" in dtbs


def test_zynq_platform_uimage_loadaddr(zynq_config_dict):
    """Test uImage load address property."""
    platform = ZynqPlatform(zynq_config_dict)
    assert platform.uimage_loadaddr == "0x8000"


def test_zynq_platform_repr(zynq_config_dict):
    """Test string representation."""
    platform = ZynqPlatform(zynq_config_dict)
    repr_str = repr(platform)

    assert "ZynqPlatform" in repr_str
    assert "arm" in repr_str
    assert "uImage" in repr_str


def test_zynq_get_dtb_make_target(zynq_config_dict):
    """Test DTB make target has no subdirectory for Zynq."""
    platform = ZynqPlatform(zynq_config_dict)

    # Zynq DTBs should have no prefix
    make_target = platform.get_dtb_make_target("zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb")
    assert make_target == "zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb"
