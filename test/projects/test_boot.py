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

    def test_build_from_source_calls_sub_builders(self, tmp_path, mocker):
        """Verify that ATFBuilder and UBootBuilder are called when paths are not provided."""
        config, platform = _make_config("zynqmp", "arm64")
        config.set("build.output_dir", str(tmp_path / "build"))
        config.set("boot.xsa_path", "/tmp/test.xsa")
        
        # Ensure paths are NOT in config
        config.set("boot.atf_path", None)
        config.set("boot.uboot_path", None)
        config.set("boot.fsbl_path", None)
        config.set("boot.pmufw_path", None)
        
        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")
        
        # Mock class builders
        mock_atf_cls = mocker.patch("adibuild.projects.boot.ATFBuilder")
        mock_uboot_cls = mocker.patch("adibuild.projects.boot.UBootBuilder")
        
        mock_atf = mock_atf_cls.return_value
        mock_atf.build.return_value = {"artifacts": {"bl31": "/tmp/bl31.elf"}}
        
        mock_uboot = mock_uboot_cls.return_value
        mock_uboot.build.return_value = {"artifacts": {"u-boot.elf": "/tmp/u-boot.elf"}}
        
        # Mock xsct calls for FSBL/PMUFW
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        # Create dummy FSBL/PMUFW output files to satisfy builder checks
        fsbl_elf = builder.source_dir / "fsbl" / "executable.elf"
        fsbl_elf.parent.mkdir(parents=True, exist_ok=True)
        fsbl_elf.write_text("dummy")
        
        pmufw_elf = builder.source_dir / "pmufw" / "executable.elf"
        pmufw_elf.parent.mkdir(parents=True, exist_ok=True)
        pmufw_elf.write_text("dummy")
        
        builder.build()
        
        # Verify ATF and U-Boot builders were instantiated and called
        mock_atf_cls.assert_called_once()
        mock_atf.build.assert_called_once()
        
        mock_uboot_cls.assert_called_once()
        mock_uboot.build.assert_called_once()
        
        # Verify xsct was called for FSBL and PMUFW
        assert any("xsct" in str(call) and "gen_fsbl.tcl" in str(call) for call in mock_execute.call_args_list)
        assert any("xsct" in str(call) and "gen_pmufw.tcl" in str(call) for call in mock_execute.call_args_list)

    def test_versal_build_from_source(self, tmp_path, mocker):
        """Verify Versal PLM/PSMFW generation from source."""
        config, platform = _make_config("versal", "arm64")
        config.set("build.output_dir", str(tmp_path / "build"))
        config.set("boot.pdi_path", "/tmp/test.pdi")
        
        config.set("boot.plm_path", None)
        config.set("boot.psmfw_path", None)
        
        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")
        
        # Mock components that we don't want to build for real here
        mocker.patch.object(builder, "_ensure_atf", return_value=Path("/tmp/bl31.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        # Create dummy PLM/PSMFW output files
        plm_elf = builder.source_dir / "plm" / "executable.elf"
        plm_elf.parent.mkdir(parents=True, exist_ok=True)
        plm_elf.write_text("dummy")
        
        psmfw_elf = builder.source_dir / "psmfw" / "executable.elf"
        psmfw_elf.parent.mkdir(parents=True, exist_ok=True)
        psmfw_elf.write_text("dummy")
        
        builder.build()
        
        # Verify xsct was called for PLM and PSMFW
        assert any("xsct" in str(call) and "gen_plm.tcl" in str(call) for call in mock_execute.call_args_list)
        assert any("xsct" in str(call) and "gen_psmfw.tcl" in str(call) for call in mock_execute.call_args_list)
