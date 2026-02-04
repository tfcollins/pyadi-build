"""CLI-specific fixtures for pytest."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from adibuild.core.toolchain import ToolchainInfo


@pytest.fixture
def cli_runner():
    """Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_config_file(tmp_path):
    """Create a temporary valid config file."""
    config_file = tmp_path / "test_config.yaml"
    config_content = """project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2

build:
  parallel_jobs: 4
  clean_before: false
  output_dir: ./build

platforms:
  zynq:
    arch: arm
    cross_compile: arm-linux-gnueabihf-
    defconfig: zynq_xcomm_adv7511_defconfig
    kernel_target: uImage
    uimage_loadaddr: '0x8000'
    dtb_path: arch/arm/boot/dts
    kernel_image_path: arch/arm/boot/uImage
    dtbs:
      - zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
      - zynq-zc706-adv7511-ad9361-fmcomms2-3.dtb
    toolchain:
      preferred: vivado
      fallback:
        - arm
        - system

  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
    dtb_path: arch/arm64/boot/dts/xilinx
    kernel_image_path: arch/arm64/boot/Image
    dtbs:
      - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
      - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
    toolchain:
      preferred: vivado
      fallback:
        - arm
        - system
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_invalid_config_file(tmp_path):
    """Create a temporary invalid config file."""
    config_file = tmp_path / "invalid_config.yaml"
    config_content = """project: linux
# Missing required fields
platforms: {}
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_build_success(mocker, tmp_path):
    """Mock successful build workflow."""
    # Create mock build output directory
    build_output = tmp_path / "build_output"
    build_output.mkdir()

    # Create mock artifacts
    kernel_image = build_output / "Image"
    kernel_image.write_text("mock kernel")

    dtb_file = build_output / "test.dtb"
    dtb_file.write_text("mock dtb")

    # Mock the build result
    mock_result = {
        "success": True,
        "duration": 123.4,
        "kernel_image": str(kernel_image),
        "dtbs": [str(dtb_file)],
        "artifacts_dir": build_output,
        "platform": "zynqmp",
    }

    # Mock LinuxBuilder.build()
    mocker.patch("adibuild.projects.linux.LinuxBuilder.build", return_value=mock_result)

    return mock_result


@pytest.fixture
def mock_build_failure(mocker):
    """Mock failed build workflow."""
    from adibuild.core.executor import BuildError

    # Mock LinuxBuilder.build() to raise BuildError
    mocker.patch(
        "adibuild.projects.linux.LinuxBuilder.build",
        side_effect=BuildError("Compilation failed: undefined reference to foo"),
    )


@pytest.fixture
def mock_toolchain_vivado(mocker):
    """Mock Vivado toolchain detection."""
    vivado_info = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vitis/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )

    mocker.patch(
        "adibuild.core.toolchain.VivadoToolchain.detect", return_value=vivado_info
    )
    mocker.patch("adibuild.core.toolchain.ArmToolchain.detect", return_value=None)
    mocker.patch("adibuild.core.toolchain.SystemToolchain.detect", return_value=None)

    return vivado_info


@pytest.fixture
def mock_toolchain_all(mocker):
    """Mock all toolchains detected."""
    vivado_info = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vitis/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )

    arm_info = ToolchainInfo(
        type="arm",
        version="11.3.0",
        path=Path("/opt/arm-gnu-toolchain"),
        env_vars={},
        cross_compile_arm32="arm-none-linux-gnueabihf-",
        cross_compile_arm64="aarch64-none-linux-gnu-",
    )

    system_info = ToolchainInfo(
        type="system",
        version="11.4.0",
        path=None,
        env_vars={},
        cross_compile_arm32=None,
        cross_compile_arm64="aarch64-linux-gnu-",
    )

    mocker.patch(
        "adibuild.core.toolchain.VivadoToolchain.detect", return_value=vivado_info
    )
    mocker.patch("adibuild.core.toolchain.ArmToolchain.detect", return_value=arm_info)
    mocker.patch(
        "adibuild.core.toolchain.SystemToolchain.detect", return_value=system_info
    )

    return {"vivado": vivado_info, "arm": arm_info, "system": system_info}


@pytest.fixture
def mock_toolchain_none(mocker):
    """Mock no toolchains detected."""
    mocker.patch("adibuild.core.toolchain.VivadoToolchain.detect", return_value=None)
    mocker.patch("adibuild.core.toolchain.ArmToolchain.detect", return_value=None)
    mocker.patch("adibuild.core.toolchain.SystemToolchain.detect", return_value=None)


@pytest.fixture
def mock_linux_builder(mocker, tmp_path):
    """Mock LinuxBuilder for various operations."""
    # Mock all LinuxBuilder methods
    mocker.patch("adibuild.projects.linux.LinuxBuilder.prepare_source")
    mocker.patch("adibuild.projects.linux.LinuxBuilder.configure")
    mocker.patch("adibuild.projects.linux.LinuxBuilder.menuconfig")
    mocker.patch("adibuild.projects.linux.LinuxBuilder.build_dtbs")
    mocker.patch("adibuild.projects.linux.LinuxBuilder.clean")

    # Return the mocked class
    return mocker.patch("adibuild.projects.linux.LinuxBuilder")


@pytest.fixture
def mock_config_loading(mocker, mock_config_file):
    """Mock config loading to return a valid config."""
    from adibuild.core.config import BuildConfig

    # Create a valid config object
    config_data = {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": "2023_R2",
        "build": {
            "parallel_jobs": 4,
            "clean_before": False,
            "output_dir": "./build",
        },
        "platforms": {
            "zynq": {
                "arch": "arm",
                "cross_compile": "arm-linux-gnueabihf-",
                "defconfig": "zynq_xcomm_adv7511_defconfig",
                "kernel_target": "uImage",
                "uimage_loadaddr": "0x8000",
                "dtb_path": "arch/arm/boot/dts",
                "kernel_image_path": "arch/arm/boot/uImage",
                "dtbs": ["zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb"],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": ["arm", "system"],
                },
            },
            "zynqmp": {
                "arch": "arm64",
                "cross_compile": "aarch64-linux-gnu-",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
                "dtb_path": "arch/arm64/boot/dts/xilinx",
                "kernel_image_path": "arch/arm64/boot/Image",
                "dtbs": ["zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb"],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": ["arm", "system"],
                },
            },
            "microblaze": {
                "arch": "microblaze",
                "cross_compile": "microblaze-xilinx-linux-gnu-",
                "defconfig": "adi_mb_defconfig",
                "kernel_target": "simpleImage.vcu118",
                "kernel_image_path": "arch/microblaze/boot/simpleImage.vcu118",
                "simpleimage_targets": ["simpleImage.vcu118"],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": [],
                },
            },
        },
    }

    config = BuildConfig.from_dict(config_data)

    # Mock load_config_with_overrides to return our config
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=config)

    return config


@pytest.fixture
def mock_schema_file(tmp_path):
    """Create a temporary schema file for validation tests."""
    schema_file = tmp_path / "config_schema.yaml"
    schema_content = """$schema: http://json-schema.org/draft-07/schema#
type: object
required:
  - project
  - repository
  - platforms
properties:
  project:
    type: string
  repository:
    type: string
  tag:
    type: string
  platforms:
    type: object
"""
    schema_file.write_text(schema_content)
    return schema_file
