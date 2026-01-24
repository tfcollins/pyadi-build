"""Real kernel build tests for Zynq platform (ARM32)."""

import json
from pathlib import Path

import pytest

from adibuild import LinuxBuilder
from adibuild.core.config import BuildConfig
from adibuild.platforms.zynq import ZynqPlatform


@pytest.mark.real_build
@pytest.mark.slow
class TestRealZynqBuild:
    """Real kernel build tests for Zynq (ARM32)."""

    def test_full_zynq_build(
        self,
        minimal_zynq_config,
        real_toolchain_arm32,
        check_disk_space,
        check_network,
    ):
        """Test complete Zynq kernel build pipeline."""
        # Create config and platform
        config = BuildConfig.from_dict(minimal_zynq_config)
        platform_config = config.get_platform("zynq")
        platform = ZynqPlatform(platform_config)

        # Create builder
        builder = LinuxBuilder(config, platform)

        # Validate environment
        builder.validate_environment()

        # Prepare source (clone/fetch ADI Linux repo)
        source_dir = builder.prepare_source()
        assert source_dir.exists()
        assert (source_dir / "Makefile").exists()
        assert (source_dir / "arch" / "arm").exists()

        # Configure kernel
        builder.configure()
        assert (source_dir / ".config").exists()

        # Build kernel image
        kernel_image = builder.build_kernel()
        assert kernel_image.exists()
        assert kernel_image.name == "uImage"

        # Verify kernel image is valid (check size and magic)
        assert kernel_image.stat().st_size > 1_000_000  # > 1MB
        with open(kernel_image, "rb") as f:
            magic = f.read(4)
            assert magic == b"\x27\x05\x19\x56"  # U-Boot magic

        # Build DTBs
        dtbs = builder.build_dtbs()
        assert len(dtbs) >= 1
        for dtb in dtbs:
            assert dtb.exists()
            assert dtb.suffix == ".dtb"
            assert dtb.stat().st_size > 1000  # > 1KB

            # Verify DTB magic
            with open(dtb, "rb") as f:
                magic = f.read(4)
                assert magic == b"\xd0\x0d\xfe\xed"  # DTB magic

        # Package artifacts
        output_dir = builder.package_artifacts(kernel_image, dtbs)
        assert output_dir.exists()

        # Verify packaged artifacts
        assert (output_dir / "uImage").exists()
        assert (output_dir / "dts").exists()
        assert (output_dir / "metadata.json").exists()

        # Verify metadata
        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)
            assert metadata["project"] == "linux"
            assert metadata["platform"] == "arm"
            assert metadata["tag"] == "2023_R2"
            assert "commit_sha" in metadata
            assert len(metadata["artifacts"]["dtbs"]) >= 1

    def test_zynq_build_with_clean(
        self,
        minimal_zynq_config,
        real_toolchain_arm32,
        check_disk_space,
        check_network,
    ):
        """Test Zynq build with clean flag."""
        config = BuildConfig.from_dict(minimal_zynq_config)
        platform_config = config.get_platform("zynq")
        platform = ZynqPlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        # Prepare and configure
        builder.prepare_source()
        builder.configure()

        # Create dummy .o file to verify clean
        source_dir = builder.source_dir
        dummy_obj = source_dir / "kernel" / "dummy.o"
        dummy_obj.parent.mkdir(parents=True, exist_ok=True)
        dummy_obj.touch()

        # Clean
        builder.clean()

        # Verify clean removed object files
        assert not dummy_obj.exists()

    def test_zynq_dtbs_only(
        self,
        minimal_zynq_config,
        real_toolchain_arm32,
        check_disk_space,
        check_network,
    ):
        """Test building only DTBs without kernel."""
        config = BuildConfig.from_dict(minimal_zynq_config)
        platform_config = config.get_platform("zynq")
        platform = ZynqPlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        # Prepare and configure
        builder.prepare_source()
        builder.configure()

        # Build only DTBs
        dtbs = builder.build_dtbs()
        assert len(dtbs) >= 1

        for dtb in dtbs:
            assert dtb.exists()
            assert dtb.stat().st_size > 1000
