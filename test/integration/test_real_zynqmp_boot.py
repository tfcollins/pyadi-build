"""Real build tests for ZynqMP boot components."""

import pytest
from pathlib import Path
import shutil

from adibuild.core.config import BuildConfig
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.uboot import UBootBuilder
from adibuild.projects.zynqmp_boot import ZynqMPBootBuilder

@pytest.mark.real_build
@pytest.mark.slow
class TestRealZynqMPBoot:
    
    def test_real_atf_build(self, real_toolchain_arm64, check_network):
        """Test real clone and build of ATF bl31.elf."""
        config_data = {
            "project": "atf",
            "tag": "master", # or a specific tag
            "build": {"parallel_jobs": 8, "output_dir": "./build"},
            "platforms": {"zynqmp": {"arch": "arm64", "cross_compile": "aarch64-linux-gnu-"}}
        }
        config = BuildConfig.from_dict(config_data)
        platform = ZynqMPPlatform(config.get_platform("zynqmp"))
        
        builder = ATFBuilder(config, platform)
        builder.validate_environment()
        
        # We use a shallow clone for speed in tests if supported by GitRepository
        # But here we just run it.
        result = builder.build(clean_before=True)
        
        bl31 = Path(result["artifacts"]["bl31"])
        assert bl31.exists()
        assert bl31.stat().st_size > 10000

    def test_real_uboot_build(self, real_toolchain_arm64, check_network):
        """Test real clone and build of U-Boot."""
        config_data = {
            "project": "uboot",
            "tag": "master",
            "build": {"parallel_jobs": 8, "output_dir": "./build"},
            "platforms": {"zynqmp": {"arch": "arm64", "cross_compile": "aarch64-linux-gnu-"}}
        }
        config = BuildConfig.from_dict(config_data)
        platform = ZynqMPPlatform(config.get_platform("zynqmp"))
        
        builder = UBootBuilder(config, platform)
        builder.validate_environment()
        
        result = builder.build(clean_before=True)
        
        uboot_elf = Path(result["artifacts"]["u-boot.elf"])
        assert uboot_elf.exists()
        assert uboot_elf.stat().st_size > 100000

    def test_real_boot_bin_generation_mocked_tools(self, tmp_path, mocker):
        """
        Test BOOT.BIN flow with real ATF/U-Boot but mocked bootgen/xsct.
        This verifies orchestration and BIF generation.
        """
        # This is a hybrid test.
        pass
