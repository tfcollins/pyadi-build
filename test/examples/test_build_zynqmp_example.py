"""Test examples/build_zynqmp_kernel.py"""

import sys
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
sys.path.insert(0, str(EXAMPLES_DIR))


class TestBuildZynqMPExample:
    """Test examples/build_zynqmp_kernel.py"""

    def test_example_imports(self):
        """Verify example can import required modules."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqMPPlatform

        assert LinuxBuilder is not None
        assert BuildConfig is not None
        assert ZynqMPPlatform is not None

    def test_config_loading_zynqmp(self):
        """Test loading ZynqMP config from YAML."""
        from adibuild import BuildConfig

        config_path = Path("configs/linux/2023_R2.yaml")
        config = BuildConfig.from_yaml(config_path)

        assert "zynqmp" in config.get("platforms", {})
        platform_config = config.get_platform("zynqmp")
        assert platform_config["arch"] == "arm64"

    def test_platform_creation_zynqmp(self, zynqmp_config_dict):
        """Test creating ZynqMPPlatform as example does."""
        from adibuild.platforms import ZynqMPPlatform

        platform = ZynqMPPlatform(zynqmp_config_dict)

        assert platform.arch == "arm64"
        assert platform.defconfig == "adi_zynqmp_defconfig"
        assert platform.kernel_target == "Image"

    def test_build_method_single_call(
        self,
        mocker,
        mock_git_repo_for_examples,
        tmp_path,
        zynqmp_config_dict,
        mock_kernel_source,
    ):
        """Test builder.build() single call as in example."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqMPPlatform

        # Create config
        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "build")},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        # Setup mocks
        mocker.patch("adibuild.core.executor.BuildExecutor.make")
        mocker.patch("adibuild.core.executor.BuildExecutor.check_tools")

        # Create DTBs
        dtb_dir = mock_kernel_source / "arch/arm64/boot/dts/xilinx"
        for dtb in zynqmp_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy")

        # Run example
        platform = ZynqMPPlatform(zynqmp_config_dict)
        builder = LinuxBuilder(config, platform)

        result = builder.build(clean_before=False)

        # Verify result structure as example expects
        assert result["success"] is True
        assert "duration" in result
        assert "kernel_image" in result
        assert "dtbs" in result
        assert "artifacts" in result

    def test_result_structure(
        self,
        mocker,
        mock_git_repo_for_examples,
        tmp_path,
        zynqmp_config_dict,
        mock_kernel_source,
    ):
        """Test that result dict has expected fields."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqMPPlatform

        # Setup (same as above)
        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "build")},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        mocker.patch("adibuild.core.executor.BuildExecutor.make")
        mocker.patch("adibuild.core.executor.BuildExecutor.check_tools")

        # Create DTBs
        dtb_dir = mock_kernel_source / "arch/arm64/boot/dts/xilinx"
        for dtb in zynqmp_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy")

        platform = ZynqMPPlatform(zynqmp_config_dict)
        builder = LinuxBuilder(config, platform)

        result = builder.build(clean_before=False)

        # Example expects these exact keys
        assert set(result.keys()) == {
            "success",
            "duration",
            "kernel_image",
            "dtbs",
            "artifacts",
        }
        assert isinstance(result["duration"], (int, float))
        assert result["duration"] > 0

    @pytest.mark.integration
    def test_full_zynqmp_workflow(
        self,
        mocker,
        mock_git_repo_for_examples,
        tmp_path,
        zynqmp_config_dict,
        mock_kernel_source,
    ):
        """Test complete ZynqMP build workflow."""
        from adibuild import BuildConfig, LinuxBuilder
        from adibuild.platforms import ZynqMPPlatform

        # Create config
        config_data = {
            "project": "linux",
            "repository": "https://github.com/analogdevicesinc/linux.git",
            "tag": "2023_R2",
            "build": {"parallel_jobs": 4, "output_dir": str(tmp_path / "build")},
            "platforms": {"zynqmp": zynqmp_config_dict},
        }
        config = BuildConfig.from_dict(config_data)

        # Setup mocks
        mocker.patch("adibuild.core.executor.BuildExecutor.make")
        mocker.patch("adibuild.core.executor.BuildExecutor.check_tools")

        # Create DTBs
        dtb_dir = mock_kernel_source / "arch/arm64/boot/dts/xilinx"
        for dtb in zynqmp_config_dict["dtbs"]:
            (dtb_dir / dtb).write_text("dummy")

        # Run workflow
        platform_config = config.get_platform("zynqmp")
        platform = ZynqMPPlatform(platform_config)
        builder = LinuxBuilder(config, platform)

        result = builder.build(clean_before=False)

        # Verify complete result
        assert result["success"] is True
        assert result["kernel_image"].exists()
        assert len(result["dtbs"]) > 0
        assert result["artifacts"].exists()
        assert (result["artifacts"] / "Image").exists()
        assert (result["artifacts"] / "metadata.json").exists()
