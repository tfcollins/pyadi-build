"""Unit tests for ZynqMPBootBuilder."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.zynqmp_boot import ZynqMPBootBuilder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(extra=None):
    """Build a minimal BuildConfig for boot tests."""
    platform_cfg = {
        "arch": "arm64",
        "cross_compile": "aarch64-linux-gnu-",
        "defconfig": "adi_zynqmp_defconfig",
        "kernel_target": "Image",
    }
    if extra:
        platform_cfg.update(extra)
        
    data = {
        "project": "boot",
        "tag": "main",
        "build": {"parallel_jobs": 4, "output_dir": "./build"},
        "platforms": {"zynqmp": platform_cfg},
        "boot": {
            "xsa_path": "/tmp/test.xsa",
            "atf_path": "/tmp/bl31.elf",
            "uboot_path": "/tmp/u-boot.elf"
        }
    }
    return BuildConfig.from_dict(data), ZynqMPPlatform(platform_cfg)


# ---------------------------------------------------------------------------
# TestZynqMPBootBuilder
# ---------------------------------------------------------------------------


class TestZynqMPBootBuilder:
    def _make_builder(self, tmp_path, extra=None):
        config, platform = _make_config(extra=extra)
        # Fix output_dir to use tmp_path
        config.set("build.output_dir", str(tmp_path / "build"))
        builder = ZynqMPBootBuilder(config, platform, work_dir=tmp_path / "work")
        return builder, config, platform

    def test_builder_init(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        assert builder.source_dir.exists()

    def test_ensure_fsbl_uses_xsct(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        # Create a dummy executable.elf to simulate XSCT success
        fsbl_dir = builder.source_dir / "fsbl"
        fsbl_dir.mkdir(parents=True)
        dummy_elf = fsbl_dir / "executable.elf"
        dummy_elf.write_text("dummy")
        
        result = builder._ensure_fsbl("/tmp/test.xsa")
        
        assert result == dummy_elf
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0][0]
        assert "xsct" in args

    def test_ensure_pmufw_uses_xsct(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        # Create a dummy executable.elf to simulate XSCT success
        pmufw_dir = builder.source_dir / "pmufw"
        pmufw_dir.mkdir(parents=True)
        dummy_elf = pmufw_dir / "executable.elf"
        dummy_elf.write_text("dummy")
        
        result = builder._ensure_pmufw("/tmp/test.xsa")
        
        assert result == dummy_elf
        mock_execute.assert_called_once()
        args = mock_execute.call_args[0][0]
        assert "xsct" in args

    def test_generate_bif(self, tmp_path):
        builder, _, _ = self._make_builder(tmp_path)
        
        bif = builder._generate_bif(
            fsbl=Path("/tmp/fsbl.elf"),
            pmufw=Path("/tmp/pmufw.elf"),
            atf=Path("/tmp/bl31.elf"),
            uboot=Path("/tmp/u-boot.elf"),
            bitstream="/tmp/system.bit"
        )
        
        assert bif.exists()
        content = bif.read_text()
        assert "[bootloader, destination_cpu=a53-0] /tmp/fsbl.elf" in content
        assert "[pmufw_image] /tmp/pmufw.elf" in content
        assert "[destination_device=pl] /tmp/system.bit" in content
        assert "bl31.elf" in content
        assert "u-boot.elf" in content

    def test_build_full_flow(self, tmp_path, mocker):
        builder, _, _ = self._make_builder(tmp_path)
        
        # Mock component builds
        mocker.patch.object(builder, "_ensure_fsbl", return_value=Path("/tmp/fsbl.elf"))
        mocker.patch.object(builder, "_ensure_pmufw", return_value=Path("/tmp/pmufw.elf"))
        mocker.patch.object(builder, "_ensure_atf", return_value=Path("/tmp/bl31.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
        
        mock_execute = mocker.patch.object(builder.executor, "execute")
        
        result = builder.build()
        
        assert "boot_bin" in result
        assert mock_execute.called
        
        # Last call should be bootgen
        args = mock_execute.call_args[0][0]
        assert "bootgen" in args
        assert "-arch" in args
        assert "zynqmp" in args

    def test_auto_detect_xsa_and_bit(self, tmp_path, mocker):
        builder, config, _ = self._make_builder(tmp_path)
        
        # Remove explicit paths from config to force auto-detect
        config.set("boot.xsa_path", None)
        config.set("boot.bit_path", None)
        
        # Create dummy artifacts in build dir
        build_dir = tmp_path / "build"
        build_dir.mkdir()
        hdl_artifacts = build_dir / "hdl_out"
        hdl_artifacts.mkdir()
        (hdl_artifacts / "system_top.xsa").write_text("xsa")
        (hdl_artifacts / "system_top.bit").write_text("bit")
        
        # Mock component builds
        mocker.patch.object(builder, "_ensure_fsbl", return_value=Path("/tmp/fsbl.elf"))
        mocker.patch.object(builder, "_ensure_pmufw", return_value=Path("/tmp/pmufw.elf"))
        mocker.patch.object(builder, "_ensure_atf", return_value=Path("/tmp/bl31.elf"))
        mocker.patch.object(builder, "_ensure_uboot", return_value=Path("/tmp/u-boot.elf"))
        
        mocker.patch.object(builder.executor, "execute")
        
        # Capture the BIF content
        def mock_gen_bif(**kwargs):
            return Path("/tmp/boot.bif")
            
        mocker.patch.object(builder, "_generate_bif", side_effect=builder._generate_bif)
        
        builder.build()
        
        # Verify bitstream was detected and included in BIF
        args, kwargs = builder._generate_bif.call_args
        assert "system_top.bit" in str(kwargs.get("bitstream"))
