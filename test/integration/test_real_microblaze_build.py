"""Real kernel build tests for MicroBlaze platform (soft-core)."""

import json

import pytest

from adibuild import LinuxBuilder
from adibuild.core.config import BuildConfig
from adibuild.platforms.microblaze import MicroBlazePlatform


@pytest.mark.real_build
@pytest.mark.slow
@pytest.mark.requires_vivado
class TestRealMicroBlazeBuild:
    """Real kernel build tests for MicroBlaze (soft-core)."""

    def test_full_microblaze_build(
        self,
        minimal_microblaze_config,
        real_toolchain_microblaze,
        check_disk_space,
        check_network,
    ):
        """Test complete MicroBlaze kernel build pipeline."""
        # Create config and platform
        config = BuildConfig.from_dict(minimal_microblaze_config)
        platform_config = config.get_platform("microblaze_vcu118")
        platform = MicroBlazePlatform(platform_config)

        # Create builder
        builder = LinuxBuilder(config, platform)

        # Validate environment
        builder.validate_environment()

        # Prepare source (clone/fetch ADI Linux repo)
        source_dir = builder.prepare_source()
        assert source_dir.exists()
        assert (source_dir / "Makefile").exists()
        assert (source_dir / "arch" / "microblaze").exists()

        # Configure kernel
        builder.configure()
        assert (source_dir / ".config").exists()

        # Build kernel (returns list of simpleImages)
        kernel_images = builder.build_kernel()
        assert isinstance(kernel_images, list)
        assert len(kernel_images) >= 1

        for img in kernel_images:
            assert img.exists()
            assert "simpleImage" in img.name
            assert img.stat().st_size > 1_000_000  # > 1MB

        # DTBs should be empty (embedded in simpleImage)
        dtbs = builder.build_dtbs()
        assert dtbs == []

        # Package artifacts
        output_dir = builder.package_artifacts(kernel_images, dtbs)
        assert output_dir.exists()

        # Verify no separate DTB directory
        assert not (output_dir / "dts").exists()

        # Verify kernel images are in output
        for img in kernel_images:
            assert (output_dir / img.name).exists()

        # Verify metadata
        assert (output_dir / "metadata.json").exists()
        with open(output_dir / "metadata.json") as f:
            metadata = json.load(f)
            assert metadata["project"] == "linux"
            assert metadata["platform"] == "microblaze"
            assert metadata["tag"] == "2023_R2"
            assert "commit_sha" in metadata
            assert len(metadata["artifacts"]["kernel_images"]) >= 1
            assert metadata["artifacts"]["dtbs"] == []

    def test_microblaze_build_with_clean(
        self,
        minimal_microblaze_config,
        real_toolchain_microblaze,
        check_disk_space,
        check_network,
    ):
        """Test MicroBlaze build with clean flag."""
        config = BuildConfig.from_dict(minimal_microblaze_config)
        platform_config = config.get_platform("microblaze_vcu118")
        platform = MicroBlazePlatform(platform_config)
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

    def test_microblaze_simpleimage_only(
        self,
        minimal_microblaze_config,
        real_toolchain_microblaze,
        check_disk_space,
        check_network,
    ):
        """Test building only simpleImage without separate DTBs."""
        config = BuildConfig.from_dict(minimal_microblaze_config)
        platform_config = config.get_platform("microblaze_vcu118")
        platform = MicroBlazePlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        # Prepare and configure
        builder.prepare_source()
        builder.configure()

        # Build kernel (simpleImage with embedded DT)
        kernel_images = builder.build_kernel()
        assert isinstance(kernel_images, list)
        assert len(kernel_images) >= 1

        for img in kernel_images:
            assert img.exists()
            assert "simpleImage" in img.name
            assert img.stat().st_size > 1_000_000  # > 1MB

        # DTBs should be empty for MicroBlaze
        dtbs = builder.build_dtbs()
        assert dtbs == []
