"""Test examples/custom_config.py"""

import sys
from pathlib import Path
import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))


class TestCustomConfigExample:
    """Test examples/custom_config.py"""

    def test_config_override_with_set(self):
        """Test using config.set() to override values."""
        from adibuild import BuildConfig

        config_path = Path("configs/linux/zynqmp.yaml")
        config = BuildConfig.from_yaml(config_path)

        # Override tag as example does
        config.set("tag", "2023_R2")

        assert config.get("tag") == "2023_R2"

    def test_menuconfig_call(self, mocker, mock_git_repo_for_examples, zynqmp_config_dict, mock_kernel_source):
        """Test calling builder.menuconfig() as in example."""
        from adibuild import LinuxBuilder, BuildConfig
        from adibuild.platforms import ZynqMPPlatform

        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        # Mock make to avoid actual menuconfig
        mock_make = mocker.patch("adibuild.core.executor.BuildExecutor.make")

        platform = ZynqMPPlatform(zynqmp_config_dict)
        builder = LinuxBuilder(config, platform)
        builder.source_dir = mock_kernel_source
        builder._configured = True

        # Call menuconfig as example does
        builder.menuconfig()

        # Verify make was called with menuconfig target
        mock_make.assert_called_once()
        call_args = mock_make.call_args
        assert "menuconfig" in str(call_args)

    def test_configure_then_menuconfig(
        self, mocker, mock_git_repo_for_examples, zynqmp_config_dict, mock_kernel_source
    ):
        """Test defconfig followed by menuconfig workflow."""
        from adibuild import LinuxBuilder, BuildConfig
        from adibuild.platforms import ZynqMPPlatform

        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        mock_make = mocker.patch("adibuild.core.executor.BuildExecutor.make")

        platform = ZynqMPPlatform(zynqmp_config_dict)
        builder = LinuxBuilder(config, platform)
        builder.source_dir = mock_kernel_source

        # Configure then menuconfig
        builder.configure()
        builder.menuconfig()

        # Both should call make
        assert mock_make.call_count == 2

    @pytest.mark.integration
    def test_full_custom_config_workflow(
        self, mocker, mock_git_repo_for_examples, tmp_path, zynqmp_config_dict, mock_kernel_source
    ):
        """Test complete custom config workflow from example."""
        from adibuild import LinuxBuilder, BuildConfig
        from adibuild.platforms import ZynqMPPlatform

        # Load and override config as example does
        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "build")},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)
        config.set("tag", "2023_R2")  # Override as example does

        # Setup mocks
        mocker.patch("adibuild.core.executor.BuildExecutor.make")
        mocker.patch("adibuild.core.executor.BuildExecutor.check_tools")

        # Create DTBs
        dtb_dir = mock_kernel_source / "arch/arm64/boot/dts/xilinx"
        for dtb in zynqmp_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy")

        # Run workflow as in example
        platform_config = config.get_platform("zynqmp")
        platform = ZynqMPPlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        builder.prepare_source()
        builder.configure()
        builder.menuconfig()  # Custom config step
        kernel_image = builder.build_kernel()
        dtbs = builder.build_dtbs()
        output_dir = builder.package_artifacts(kernel_image, dtbs)

        # Verify workflow completed
        assert output_dir.exists()
        assert (output_dir / "Image").exists()
        assert (output_dir / "dts").exists()

    def test_config_override_verification(self):
        """Test that config overrides persist."""
        from adibuild import BuildConfig

        config_path = Path("configs/linux/zynqmp.yaml")
        config = BuildConfig.from_yaml(config_path)

        # Test multiple overrides
        config.set("tag", "2023_R2")
        config.set("build.parallel_jobs", 8)

        assert config.get("tag") == "2023_R2"
        assert config.get("build.parallel_jobs") == 8
