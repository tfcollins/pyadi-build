"""Unit tests for ATFBuilder and UBootBuilder."""

from pathlib import Path
from unittest.mock import MagicMock

from adibuild.core.config import BuildConfig
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.uboot import UBootBuilder

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(project, extra=None):
    """Build a minimal BuildConfig for tests."""
    platform_cfg = {
        "arch": "arm64",
        "cross_compile": "aarch64-linux-gnu-",
        "defconfig": "adi_zynqmp_defconfig",
        "kernel_target": "Image",
    }
    if extra:
        platform_cfg.update(extra)

    data = {
        "project": project,
        "tag": "main",
        "build": {"parallel_jobs": 4, "output_dir": "./build"},
        "platforms": {"zynqmp": platform_cfg},
    }
    return BuildConfig.from_dict(data), ZynqMPPlatform(platform_cfg)


# ---------------------------------------------------------------------------
# TestATFBuilder
# ---------------------------------------------------------------------------


class TestATFBuilder:
    def test_build_flow(self, tmp_path, mocker):
        config, platform = _make_config("atf")
        builder = ATFBuilder(config, platform, work_dir=tmp_path / "work")

        # Mock source preparation
        mocker.patch.object(builder, "prepare_source", return_value=tmp_path / "src")
        builder.source_dir = tmp_path / "src"
        builder.source_dir.mkdir()

        # Mock toolchain
        mock_tc = MagicMock()
        mock_tc.cross_compile_arm64 = "aarch64-none-elf-"
        mock_tc.env_vars = {"PATH": "/usr/bin"}
        mocker.patch.object(platform, "get_toolchain", return_value=mock_tc)

        # Mock make execution
        mock_make = mocker.patch.object(builder.executor, "make")

        # Create dummy bl31.elf
        bl31_dir = builder.source_dir / "build" / "zynqmp" / "release" / "bl31"
        bl31_dir.mkdir(parents=True)
        (bl31_dir / "bl31.elf").write_text("dummy ATF")

        result = builder.build()

        assert "bl31" in result["artifacts"]
        assert Path(result["artifacts"]["bl31"]).name == "bl31.elf"
        mock_make.assert_called_once()
        args = mock_make.call_args[1].get("extra_args")
        assert "PLAT=zynqmp" in args
        assert "bl31" in args
        assert "CROSS_COMPILE=aarch64-none-elf-" in args


# ---------------------------------------------------------------------------
# TestUBootBuilder
# ---------------------------------------------------------------------------


class TestUBootBuilder:
    def test_build_flow(self, tmp_path, mocker):
        config, platform = _make_config("uboot")
        builder = UBootBuilder(config, platform, work_dir=tmp_path / "work")

        # Mock source preparation
        mocker.patch.object(builder, "prepare_source", return_value=tmp_path / "src")
        builder.source_dir = tmp_path / "src"
        builder.source_dir.mkdir()

        # Mock toolchain environment
        mocker.patch.object(
            platform,
            "get_make_env",
            return_value={"ARCH": "arm64", "CROSS_COMPILE": "aarch64-"},
        )

        # Mock make execution
        mock_make = mocker.patch.object(builder.executor, "make")

        # Create dummy u-boot.elf
        (builder.source_dir / "u-boot.elf").write_text("dummy u-boot")

        result = builder.build()

        assert "u-boot.elf" in result["artifacts"]
        assert mock_make.call_count == 2  # configure + build

        # Check configure call
        conf_args = mock_make.call_args_list[0][0]
        assert "xilinx_zynqmp_virt_defconfig" in conf_args

        # Check env usage
        env = mock_make.call_args_list[0][1].get("env")
        assert env["ARCH"] == "arm64"
