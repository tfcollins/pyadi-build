"""Integration test fixtures for real kernel builds."""

import os
import shutil
import socket
import subprocess
from pathlib import Path

import pytest
import requests

from test.integration.docker_utils import (
    build_synthetic_vivado_installer,
    docker_vivado_cache_dir,
    docker_vivado_install_version,
    docker_vivado_version,
    keep_docker_vivado_artifacts,
    use_synthetic_vivado_installer,
)


def _probe_https_response(url: str, timeout: int = 15) -> str | None:
    """Return None when an HTTPS endpoint answers, otherwise a failure reason."""
    try:
        response = requests.get(
            url,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return f"HTTPS connectivity preflight failed for {url}: {exc}"

    response.close()
    return None


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
def real_toolchain_hdl():
    """Detect or skip if Vivado not available for HDL builds."""
    if not shutil.which("vivado"):
        pytest.skip("Vivado not found in PATH")
    return "vivado"


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
def check_docker_available():
    """Verify Docker CLI access for container-backed integration tests."""
    if not shutil.which("docker"):
        pytest.skip("Docker CLI not found")

    result = subprocess.run(
        ["docker", "info"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"Docker daemon is not available: {result.stderr.strip()}")


@pytest.fixture(scope="session")
def check_vivado_docker_network(docker_vivado_test_version):
    """Verify the Docker Vivado test has the external network access it needs."""
    for host in ("pypi.org",):
        try:
            socket.create_connection((host, 443), timeout=5)
        except OSError:
            pytest.skip(f"No network connectivity to {host}")

    return docker_vivado_test_version


@pytest.fixture(scope="session")
def check_vivado_docker_disk_space(tmp_path_factory):
    """Verify sufficient disk space for a containerized Vivado install."""
    tmp_base = tmp_path_factory.getbasetemp()
    stat = shutil.disk_usage(tmp_base)
    required_gb = 120
    available_gb = stat.free / (1024**3)

    if available_gb < required_gb:
        pytest.skip(
            f"Insufficient disk space for Docker Vivado install: "
            f"{available_gb:.1f}GB available, {required_gb}GB required"
        )


@pytest.fixture(scope="session")
def vivado_docker_credentials():
    """Provide AMD credentials or skip the Docker Vivado test."""
    username = os.environ.get("AMD_USERNAME")
    password = os.environ.get("AMD_PASSWORD")
    if not username or not password:
        pytest.skip(
            "AMD_USERNAME and AMD_PASSWORD are required for Docker Vivado install tests"
        )

    return {
        "AMD_USERNAME": username,
        "AMD_PASSWORD": password,
    }


@pytest.fixture(scope="session")
def docker_vivado_test_version():
    """Return the requested Docker Vivado test version."""
    return docker_vivado_version()


@pytest.fixture(scope="session")
def docker_vivado_test_install_version(docker_vivado_test_version):
    """Return the on-disk install version for the requested Docker test version."""
    return docker_vivado_install_version(docker_vivado_test_version)


@pytest.fixture(scope="session")
def docker_vivado_debug_keep():
    """Whether Docker artifacts should be kept for debugging."""
    return keep_docker_vivado_artifacts()


@pytest.fixture(scope="session")
def docker_vivado_installer_bundle(docker_vivado_test_version, tmp_path_factory):
    """Return real-download mode or a synthetic local installer fallback."""
    from adibuild.core.vivado import VivadoInstaller

    release = VivadoInstaller().resolve_release(docker_vivado_test_version)
    reason = None
    synthetic = use_synthetic_vivado_installer()
    if not synthetic:
        reason = _probe_https_response(release.download_url)
        synthetic = reason is not None

    if not synthetic:
        return {
            "mode": "real",
            "installer_path": None,
            "reason": None,
        }

    installer_root = tmp_path_factory.getbasetemp() / "synthetic-vivado-installer"
    installer_path = build_synthetic_vivado_installer(
        docker_vivado_test_version,
        installer_root,
    )
    return {
        "mode": "synthetic",
        "installer_path": installer_path,
        "reason": reason or "ADIBUILD_VIVADO_DOCKER_SYNTHETIC_INSTALLER requested",
    }


@pytest.fixture
def docker_vivado_host_cache_dir(tmp_path):
    """Writable host cache directory mounted into the Docker container."""
    cache_dir = docker_vivado_cache_dir(tmp_path)
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


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


@pytest.fixture
def hdl_zed_fmcomms2_config(tmp_path, real_build_config):
    """HDL configuration for Zedboard + FMCOMMS2."""
    return {
        "project": "hdl",
        "repository": "https://github.com/analogdevicesinc/hdl.git",
        "tag": "hdl_2023_r2",
        "build": {
            "parallel_jobs": real_build_config["parallel_jobs"],
            "output_dir": str(tmp_path / "build"),
        },
        "platforms": {
            "zed_fmcomms2": {
                "hdl_project": "fmcomms2",
                "carrier": "zed",
                "arch": "arm",
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
