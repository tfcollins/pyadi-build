"""Test examples/build_zynq_kernel.py"""

import sys
from pathlib import Path

import pytest

# Setup path to import examples
EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))


class TestBuildZynqExample:
    """Test examples/build_zynq_kernel.py"""

    def test_example_imports(self):
        """Verify example can import required modules."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        assert LinuxBuilder is not None
        assert BuildConfig is not None
        assert ZynqPlatform is not None

    def test_config_loading(self):
        """Test loading config from YAML as example does."""
        from adibuild import BuildConfig

        config_path = Path("configs/linux/2023_R2.yaml")
        config = BuildConfig.from_yaml(config_path)

        assert config.get("project") == "linux"
        assert config.get("tag") == "2023_R2"
        assert "zynq" in config.get("platforms", {})

    def test_platform_creation(self, zynq_config_dict):
        """Test creating ZynqPlatform as example does."""
        from adibuild.platforms import ZynqPlatform

        platform = ZynqPlatform(zynq_config_dict)

        assert platform.arch == "arm"
        assert platform.defconfig == "zynq_xcomm_adv7511_defconfig"
        assert platform.kernel_target == "uImage"

    def test_builder_initialization(self, zynq_config, zynq_config_dict):
        """Test LinuxBuilder initialization as example does."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)

        assert builder.config == zynq_config
        assert builder.platform == platform

    def test_prepare_source(
        self, mock_git_repo_for_examples, zynq_config, zynq_config_dict
    ):
        """Test prepare_source() call as in example."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)

        source_dir = builder.prepare_source()

        assert source_dir.name == "linux"
        assert builder.source_dir is not None

    def test_configure(
        self,
        mocker,
        mock_git_repo_for_examples,
        zynq_config,
        zynq_config_dict,
        mock_kernel_source,
    ):
        """Test configure() call as in example."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        # Setup mocks
        mock_make = mocker.patch("adibuild.core.executor.BuildExecutor.make")

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)
        builder.source_dir = mock_kernel_source

        builder.configure()

        # Verify make was called with defconfig
        mock_make.assert_called_once()
        assert builder._configured is True

    def test_build_kernel(
        self,
        mocker,
        mock_git_repo_for_examples,
        zynq_config,
        zynq_config_dict,
        mock_kernel_source,
    ):
        """Test build_kernel() call as in example."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        # Setup mocks
        mocker.patch("adibuild.core.executor.BuildExecutor.make")

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)
        builder.source_dir = mock_kernel_source
        builder._configured = True

        kernel_image = builder.build_kernel()

        # Verify kernel image path
        assert kernel_image == mock_kernel_source / "arch/arm/boot/uImage"
        assert kernel_image.exists()

    def test_build_dtbs(
        self,
        mocker,
        mock_git_repo_for_examples,
        zynq_config,
        zynq_config_dict,
        mock_kernel_source,
    ):
        """Test build_dtbs() call as in example."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        # Setup mocks and DTB files
        mocker.patch("adibuild.core.executor.BuildExecutor.make")

        # Create DTB files
        dtb_dir = mock_kernel_source / "arch/arm/boot/dts"
        for dtb in zynq_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy dtb")

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)
        builder.source_dir = mock_kernel_source
        builder._configured = True

        dtbs = builder.build_dtbs()

        # Verify DTB list
        assert len(dtbs) == len(zynq_config_dict["dtbs"])
        assert all(dtb.exists() for dtb in dtbs)

    def test_package_artifacts(
        self, mocker, tmp_path, zynq_config, zynq_config_dict, mock_kernel_source
    ):
        """Test package_artifacts() call as in example."""
        from adibuild import LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        # Setup
        mocker.patch("adibuild.utils.git.GitRepository")
        mock_repo = mocker.MagicMock()
        mock_repo.get_commit_sha.return_value = "abc123"

        platform = ZynqPlatform(zynq_config_dict)
        builder = LinuxBuilder(zynq_config, platform)
        builder.source_dir = mock_kernel_source
        builder.repo = mock_repo

        # Mock toolchain
        from adibuild.core.toolchain import ToolchainInfo

        builder._toolchain = ToolchainInfo(
            type="test",
            version="1.0",
            path=Path("/test"),
            env_vars={},
            cross_compile_arm32="arm-test-",
        )

        kernel_image = mock_kernel_source / "arch/arm/boot/uImage"
        dtb_dir = mock_kernel_source / "arch/arm/boot/dts"
        dtbs = [dtb_dir / dtb for dtb in zynq_config_dict["dtbs"]]

        # Create DTBs
        for dtb in dtbs:
            dtb.write_text("dummy dtb")

        # Override output dir to tmp
        zynq_config.set("build.output_dir", str(tmp_path / "build"))

        output_dir = builder.package_artifacts(kernel_image, dtbs)

        # Verify artifacts
        assert output_dir.exists()
        assert (output_dir / "uImage").exists()
        assert (output_dir / "dts").exists()
        assert (output_dir / "metadata.json").exists()

    @pytest.mark.integration
    def test_full_example_workflow(
        self,
        mocker,
        mock_git_repo_for_examples,
        tmp_path,
        zynq_config_dict,
        mock_kernel_source,
    ):
        """Test complete workflow from example (mocked)."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqPlatform

        # Create config
        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "build")},
            "platforms": {"zynq": zynq_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        # Setup mocks
        mocker.patch("adibuild.core.executor.BuildExecutor.make")

        # Create DTBs
        dtb_dir = mock_kernel_source / "arch/arm/boot/dts"
        for dtb in zynq_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy")

        # Run example workflow
        platform_config = config.get_platform("zynq")
        platform = ZynqPlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        # Execute steps as in example
        source_dir = builder.prepare_source()
        builder.configure()
        kernel_image = builder.build_kernel()
        dtbs = builder.build_dtbs()
        artifacts = builder.package_artifacts(kernel_image, dtbs)

        # Verify results
        assert source_dir is not None
        assert kernel_image.exists()
        assert len(dtbs) > 0
        assert artifacts.exists()
