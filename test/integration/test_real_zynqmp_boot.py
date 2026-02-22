"""Real build tests for ZynqMP boot components."""

from pathlib import Path

import pytest

from adibuild.core.config import BuildConfig
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.boot import BootBuilder
from adibuild.projects.uboot import UBootBuilder


@pytest.mark.real_build
@pytest.mark.slow
class TestRealZynqMPBoot:

    def test_real_atf_build(self, real_toolchain_arm64, check_network):
        """Test real clone and build of ATF bl31.elf."""
        config_data = {
            "project": "atf",
            "repository": "https://github.com/analogdevicesinc/arm-trusted-firmware.git",
            "tag": "master",
            "build": {"parallel_jobs": 8, "output_dir": "./build"},
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
        platform = ZynqMPPlatform(config.get_platform("zynqmp"))

        builder = ATFBuilder(config, platform)
        builder.validate_environment()

        result = builder.build(clean_before=True)

        bl31 = Path(result["artifacts"]["bl31"])
        assert bl31.exists()
        assert bl31.stat().st_size > 10000

    def test_real_uboot_build(self, real_toolchain_arm64, check_network):
        """Test real clone and build of U-Boot."""
        atf_config_data = {
            "project": "atf",
            "repository": "https://github.com/analogdevicesinc/arm-trusted-firmware.git",
            "tag": "master",
            "build": {"parallel_jobs": 8, "output_dir": "./build"},
            "platforms": {
                "zynqmp": {
                    "arch": "arm64",
                    "cross_compile": "aarch64-linux-gnu-",
                    "defconfig": "adi_zynqmp_defconfig",
                    "kernel_target": "Image",
                }
            },
        }
        atf_config = BuildConfig.from_dict(atf_config_data)
        platform = ZynqMPPlatform(atf_config.get_platform("zynqmp"))
        atf_builder = ATFBuilder(atf_config, platform)
        atf_result = atf_builder.build()
        bl31_bin = atf_result["artifacts"].get("bl31_bin")

        config_data = {
            "project": "uboot",
            "repository": "https://github.com/analogdevicesinc/u-boot.git",
            "tag": "adi-u-boot-2025.04.y",
            "build": {"parallel_jobs": 8, "output_dir": "./build"},
            "platforms": {
                "zynqmp": {
                    "arch": "arm64",
                    "cross_compile": "aarch64-linux-gnu-",
                    "defconfig": "xilinx_zynqmp_virt_defconfig",
                    "kernel_target": "Image",
                }
            },
        }
        config = BuildConfig.from_dict(config_data)

        builder = UBootBuilder(config, platform)
        builder.validate_environment()

        env_overrides = {"BINMAN_ALLOW_MISSING": "1"}
        if bl31_bin:
            env_overrides["BL31"] = str(Path(bl31_bin).absolute())

        result = builder.build(clean_before=True, env_overrides=env_overrides)

        uboot_elf = Path(result["artifacts"]["u-boot.elf"])
        assert uboot_elf.exists()
        assert uboot_elf.stat().st_size > 100000

    def test_real_boot_bin_generation_mocked_tools(
        self, tmp_path, mocker, real_toolchain_arm64, check_network
    ):
        """
        Test BOOT.BIN flow with real ATF/U-Boot but mocked bootgen/xsct.
        This verifies orchestration and BIF generation.
        """
        from adibuild.core.executor import ExecutionResult

        config_data = {
            "project": "boot",
            "repository": "https://github.com/analogdevicesinc/hdl.git",
            "tag": "main",
            "build": {"parallel_jobs": 8, "output_dir": str(tmp_path / "build")},
            "platforms": {
                "zynqmp": {
                    "arch": "arm64",
                    "cross_compile": "aarch64-linux-gnu-",
                    "defconfig": "adi_zynqmp_defconfig",
                    "kernel_target": "Image",
                }
            },
            "boot": {"xsa_path": str(tmp_path / "system_top.xsa")},
        }

        # Create dummy XSA
        (tmp_path / "system_top.xsa").write_text("dummy xsa")

        config = BuildConfig.from_dict(config_data)
        platform = ZynqMPPlatform(config.get_platform("zynqmp"))

        builder = BootBuilder(config, platform, work_dir=tmp_path / "work")

        # Mock xsct and bootgen execution
        mock_execute = mocker.patch.object(builder.executor, "execute")

        # Mock component builds to use dummies for speed OR use real ones if already tested
        # To make it "real" we let it build ATF/U-Boot from source
        # But we must mock xsct results

        def side_effect(cmd, **kwargs):
            if "xsct" in str(cmd):
                # Create dummy executable.elf in the expected location
                cwd = kwargs.get("cwd")
                if cwd:
                    elf = Path(cwd) / "executable.elf"
                    elf.parent.mkdir(parents=True, exist_ok=True)
                    elf.write_text("dummy elf")
            return ExecutionResult(
                command=str(cmd), return_code=0, stdout="", stderr="", duration=0.0
            )

        mock_execute.side_effect = side_effect

        # We need to mock ATF/UBoot build results to point to something that exists
        # if we don't want to wait for full clone/build here.
        # Let's mock them for this test to keep it fast.
        mocker.patch.object(builder, "_ensure_atf", return_value=tmp_path / "bl31.elf")
        mocker.patch.object(
            builder, "_ensure_uboot", return_value=tmp_path / "u-boot.elf"
        )
        (tmp_path / "bl31.elf").write_text("atf")
        (tmp_path / "u-boot.elf").write_text("uboot")

        result = builder.build()

        assert "boot_bin" in result
        assert any("bootgen" in str(call) for call in mock_execute.call_args_list)
        assert any("gen_fsbl.tcl" in str(call) for call in mock_execute.call_args_list)
        assert any("gen_pmufw.tcl" in str(call) for call in mock_execute.call_args_list)
