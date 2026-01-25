"""Real HDL build tests for Zedboard + FMCOMMS2."""

from pathlib import Path

import pytest

from adibuild.cli.helpers import get_platform_instance
from adibuild.core.config import BuildConfig
from adibuild.projects.hdl import HDLBuilder


@pytest.mark.real_build
@pytest.mark.slow
class TestRealHDLBuild:
    """Real HDL build tests."""

    def test_hdl_build_zed_fmcomms2(
        self,
        hdl_zed_fmcomms2_config,
        real_toolchain_hdl,
        check_disk_space,
        check_network,
    ):
        """Test complete HDL build for Zedboard + FMCOMMS2."""

        # Load config
        config = BuildConfig.from_dict(hdl_zed_fmcomms2_config)
        platform_name = "zed_fmcomms2"

        # Get platform instance (using helper logic to ensure HDLPlatform)
        # We need to ensure helper injects 'name'
        platform_config = config.get_platform(platform_name)
        platform_config["name"] = platform_name

        # Since we can't easily import HDLPlatform from helpers without modifying imports,
        # we'll trust get_platform_instance logic which we updated earlier.
        platform = get_platform_instance(config, platform_name)

        builder = HDLBuilder(config, platform)

        # Prepare source
        source_dir = builder.prepare_source()
        assert source_dir.exists()

        # Verify project structure
        project_dir = source_dir / "projects" / "fmcomms2" / "zed"
        assert project_dir.exists()
        assert (project_dir / "Makefile").exists()

        # Build
        # Note: This takes a LONG time (30-60+ mins) on real hardware.
        # We assume the 'slow' marker handles exclusion during normal runs.
        result = builder.build()

        # Verify artifacts
        output_dir = Path(result["output_dir"])
        assert output_dir.exists()

        artifacts = result["artifacts"]
        assert len(artifacts["xsa"]) > 0
        assert len(artifacts["bit"]) > 0

        for xsa in artifacts["xsa"]:
            assert Path(xsa).exists()
            assert Path(xsa).suffix == ".xsa"

        for bit in artifacts["bit"]:
            assert Path(bit).exists()
            assert Path(bit).suffix == ".bit"
