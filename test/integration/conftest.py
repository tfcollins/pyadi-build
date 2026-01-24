"""Integration test fixtures for real kernel builds."""

import shutil
import socket
from pathlib import Path

import pytest

from adibuild.core.config import BuildConfig


@pytest.fixture(scope="session")
def real_toolchain_arm32():
    """Detect or skip if ARM32 toolchain not available."""
    from adibuild.core.toolchain import ToolchainError, select_toolchain

    try:
        toolchain = select_toolchain("vivado", ["arm", "system"])
        if not toolchain.cross_compile_arm32:
            pytest.skip("No ARM32 toolchain available")
        return toolchain
    except (ToolchainError, Exception):
        pytest.skip("No ARM32 toolchain available")


@pytest.fixture(scope="session")
def real_toolchain_arm64():
    """Detect or skip if ARM64 toolchain not available."""
    from adibuild.core.toolchain import ToolchainError, select_toolchain

    try:
        toolchain = select_toolchain("vivado", ["arm", "system"])
        if not toolchain.cross_compile_arm64:
            pytest.skip("No ARM64 toolchain available")
        return toolchain
    except (ToolchainError, Exception):
        pytest.skip("No ARM64 toolchain available")


@pytest.fixture(scope="session")
def real_toolchain_microblaze():
    """Detect or skip if MicroBlaze toolchain not available."""
    from adibuild.core.toolchain import ToolchainError, select_toolchain

    try:
        toolchain = select_toolchain("vivado", [])
        if not toolchain.cross_compile_microblaze:
            pytest.skip("No MicroBlaze toolchain available")
        return toolchain
    except (ToolchainError, Exception):
        pytest.skip("No MicroBlaze toolchain available (requires Vivado)")


@pytest.fixture(scope="session")
def check_disk_space(tmp_path_factory):
    """Verify sufficient disk space for kernel build."""
    tmp_base = tmp_path_factory.getbasetemp()
    stat = shutil.disk_usage(tmp_base)
    required_gb = 15  # ~10GB for source + 5GB for build
    available_gb = stat.free / (1024**3)

    if available_gb < required_gb:
        pytest.skip(
            f"Insufficient disk space: {available_gb:.1f}GB available, {required_gb}GB required"
        )


@pytest.fixture(scope="session")
def check_network():
    """Verify network connectivity for git operations."""
    try:
        socket.create_connection(("github.com", 443), timeout=5)
    except OSError:
        pytest.skip("No network connectivity to github.com")


@pytest.fixture(scope="session")
def real_build_config():
    """Configuration for real builds."""
    return {
        "tag": "2023_R2",
        "parallel_jobs": 4,
        "minimal_dtbs": True,
        "output_dir": None,
    }


@pytest.fixture
def minimal_zynq_config(tmp_path, real_build_config):
    """Minimal Zynq configuration for faster builds."""
    return {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": real_build_config["tag"],
        "build": {
            "parallel_jobs": real_build_config["parallel_jobs"],
            "output_dir": str(tmp_path / "build"),
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
                "dtbs": [
                    "zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb",
                ],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": ["arm", "system"],
                },
            }
        },
    }


@pytest.fixture
def minimal_zynqmp_config(tmp_path, real_build_config):
    """Minimal ZynqMP configuration for faster builds."""
    return {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": real_build_config["tag"],
        "build": {
            "parallel_jobs": real_build_config["parallel_jobs"],
            "output_dir": str(tmp_path / "build"),
        },
        "platforms": {
            "zynqmp": {
                "arch": "arm64",
                "cross_compile": "aarch64-linux-gnu-",
                "defconfig": "adi_zynqmp_defconfig",
                "kernel_target": "Image",
                "dtb_path": "arch/arm64/boot/dts/xilinx",
                "kernel_image_path": "arch/arm64/boot/Image",
                "dtbs": [
                    "zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb",
                ],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": ["arm", "system"],
                },
            }
        },
    }


@pytest.fixture
def minimal_microblaze_config(tmp_path, real_build_config):
    """Minimal MicroBlaze configuration for faster builds."""
    return {
        "project": "linux",
        "repository": "https://github.com/analogdevicesinc/linux.git",
        "tag": real_build_config["tag"],
        "build": {
            "parallel_jobs": real_build_config["parallel_jobs"],
            "output_dir": str(tmp_path / "build"),
        },
        "platforms": {
            "microblaze_vcu118": {
                "arch": "microblaze",
                "cross_compile": "microblazeel-xilinx-linux-gnu-",
                "defconfig": "adi_mb_defconfig",
                "kernel_target": "simpleImage.vcu118_ad9081",
                "dtb_path": "arch/microblaze/boot/dts",
                "kernel_image_path": "arch/microblaze/boot/simpleImage.vcu118_ad9081",
                "simpleimage_targets": [
                    "simpleImage.vcu118_ad9081",
                ],
                "dtbs": [],
                "toolchain": {
                    "preferred": "vivado",
                    "fallback": [],
                },
            }
        },
    }


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests(request):
    """Clean up build artifacts after test session."""

    def cleanup():
        """Remove build artifacts but preserve repo cache."""
        work_dir = Path.home() / ".adibuild" / "work"
        if work_dir.exists():
            for item in work_dir.iterdir():
                if item.name.startswith("build-"):
                    try:
                        shutil.rmtree(item, ignore_errors=True)
                    except Exception:
                        pass

    request.addfinalizer(cleanup)
