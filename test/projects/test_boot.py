"""Unit tests for generic BootBuilder."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.platforms.versal import VersalPlatform
from adibuild.projects.boot import BootBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(platform_name, arch, extra=None):
    """Build a minimal BuildConfig for boot tests."""
    platform_cfg = {
        "arch": arch,
        "cross_compile": "aarch64-linux-gnu-" if arch == "arm64" else "arm-linux-gnueabihf-",
        "defconfig": "dummy_defconfig",
        "kernel_target": "Image" if arch == "arm64" else "uImage",
    }
    if extra:
        platform_cfg.update(extra)
        
    data = {
        "project": "boot",
        "tag": "main",
        "build": {"parallel_jobs": 4, "output_dir": "./build"},
        "platforms": {platform_name: platform_cfg},
    }
    
    if platform_name == "zynq":
        p_obj = ZynqPlatform(platform_cfg)
    elif platform_name == "zynqmp":
        p_obj = ZynqMPPlatform(platform_cfg)
    else:
        p_obj = VersalPlatform(platform_cfg)
        
    return BuildConfig.from_dict(data), p_obj


# ---------------------------------------------------------------------------
# TestBootBuilder
# ---------------------------------------------------------------------------


class TestBootBuilder:
    def test_zynq_flow(self, tmp_path, mocker):
        config, platform = _make_config("zynq", "arm")
        config.set("build.output_dir", str(tmp_path / "build"))
        config.set("boot.xsa_path", "/tmp/test.xsa")
        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")
        
        mocker.patch.object(builder, "_ensure_fsbl", return_value=Path("/tmp/fsbl.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
        mocker.patch.object(builder, "_find_bitstream", return_value="/tmp/system.bit")
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        result = builder.build()
        
        assert "boot_bin" in result
        args = mock_execute.call_args[0][0]
        assert "bootgen" in args
        assert "zynq" in args
        assert "zynqmp" not in args

    def test_zynqmp_flow(self, tmp_path, mocker):
        config, platform = _make_config("zynqmp", "arm64")
        config.set("build.output_dir", str(tmp_path / "build"))
        config.set("boot.xsa_path", "/tmp/test.xsa")
        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")
        
        mocker.patch.object(builder, "_ensure_fsbl", return_value=Path("/tmp/fsbl.elf"))
        mocker.patch.object(builder, "_ensure_pmufw", return_value=Path("/tmp/pmufw.elf"))
        mocker.patch.object(builder, "_ensure_atf", return_value=Path("/tmp/bl31.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
    
        mock_execute = mocker.patch.object(builder.executor, "execute")
    
        result = builder.build()
        
        assert "boot_bin" in result
        args = mock_execute.call_args[0][0]
        assert "bootgen" in args
        assert "zynqmp" in args

    def test_versal_flow(self, tmp_path, mocker):
        config, platform = _make_config("versal", "arm64")
        config.set("build.output_dir", str(tmp_path / "build"))
        config.set("boot.pdi_path", "/tmp/test.pdi")
        config.set("boot.plm_path", "/tmp/plm.elf")
        config.set("boot.psmfw_path", "/tmp/psmfw.elf")
        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")
        
        mocker.patch.object(builder, "_ensure_atf", return_value=Path("/tmp/bl31.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
        mocker.patch.object(builder, "_find_pdi", return_value=Path("/tmp/system.pdi"))
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        result = builder.build()
        
        assert "boot_bin" in result
        args = mock_execute.call_args[0][0]
        assert "bootgen" in args
        assert "versal" in args
        
        # Verify BIF content for Versal
        bif_content = Path(result["artifacts"][1]).read_text()
        assert "type=bootloader, file=/tmp/plm.elf" in bif_content
        assert "type=pdi, file=/tmp/test.pdi" in bif_content