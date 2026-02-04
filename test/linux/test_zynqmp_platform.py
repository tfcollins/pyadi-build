"""Tests for ZynqMP platform."""

import pytest

from adibuild.platforms.zynqmp import ZynqMPPlatform


def test_zynqmp_platform_init(zynqmp_config_dict):
    """Test ZynqMP platform initialization."""
    platform = ZynqMPPlatform(zynqmp_config_dict)

    assert platform.arch == "arm64"
    assert platform.cross_compile == "aarch64-linux-gnu-"
    assert platform.defconfig == "adi_zynqmp_defconfig"
    assert platform.kernel_target == "Image"


def test_zynqmp_platform_invalid_arch():
    """Test error when arch is not 'arm64'."""
    config = {
        "arch": "arm",  # Wrong arch for ZynqMP
        "cross_compile": "aarch64-linux-gnu-",
        "defconfig": "test_defconfig",
        "kernel_target": "Image",
    }

    with pytest.raises(ValueError, match="requires arch='arm64'"):
        ZynqMPPlatform(config)


def test_zynqmp_platform_get_make_env(zynqmp_config_dict, mocker):
    """Test getting make environment variables with fallback to platform config."""
    from pathlib import Path

    from adibuild.core.toolchain import ToolchainInfo

    platform = ZynqMPPlatform(zynqmp_config_dict)

    # Create a toolchain without cross_compile values to test fallback behavior
    toolchain_without_cross_compile = ToolchainInfo(
        type="mock",
        version="1.0.0",
        path=Path("/mock/toolchain"),
        env_vars={"PATH": "/mock/toolchain/bin"},
        cross_compile_arm32=None,
        cross_compile_arm64=None,  # Test fallback to platform config
    )

    # Mock get_toolchain
    mocker.patch.object(
        platform, "get_toolchain", return_value=toolchain_without_cross_compile
    )

    env = platform.get_make_env()

    assert env["ARCH"] == "arm64"
    assert env["CROSS_COMPILE"] == "aarch64-linux-gnu-"  # Should use platform config
    assert "PATH" in env


def test_zynqmp_platform_dtb_path(zynqmp_config_dict):
    """Test DTB path property."""
    platform = ZynqMPPlatform(zynqmp_config_dict)
    assert platform.dtb_path == "arch/arm64/boot/dts/xilinx"


def test_zynqmp_platform_kernel_image_path(zynqmp_config_dict):
    """Test kernel image path property."""
    platform = ZynqMPPlatform(zynqmp_config_dict)
    assert platform.kernel_image_path == "arch/arm64/boot/Image"


def test_zynqmp_platform_dtbs(zynqmp_config_dict):
    """Test DTB list property."""
    platform = ZynqMPPlatform(zynqmp_config_dict)
    dtbs = platform.dtbs

    assert len(dtbs) == 2
    assert "zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb" in dtbs


def test_zynqmp_platform_repr(zynqmp_config_dict):
    """Test string representation."""
    platform = ZynqMPPlatform(zynqmp_config_dict)
    repr_str = repr(platform)

    assert "ZynqMPPlatform" in repr_str
    assert "arm64" in repr_str
    assert "Image" in repr_str


def test_zynqmp_get_dtb_make_target(zynqmp_config_dict):
    """Test DTB make target includes xilinx subdirectory."""
    platform = ZynqMPPlatform(zynqmp_config_dict)

    # ZynqMP DTBs should have xilinx/ prefix
    make_target = platform.get_dtb_make_target(
        "zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb"
    )
    assert make_target == "xilinx/zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb"
