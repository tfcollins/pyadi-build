"""Pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from adibuild.core.config import BuildConfig
from adibuild.core.toolchain import ToolchainInfo


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--real-build",
        action="store_true",
        default=False,
        help="Run real build integration tests (slow, requires toolchains)",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on options."""
    # Skip real_build tests by default
    if not config.getoption("--real-build"):
        skip_real_build = pytest.mark.skip(
            reason="--real-build flag not provided. Use 'pytest --real-build' to run real build tests"
        )
        for item in items:
            if "real_build" in item.keywords:
                item.add_marker(skip_real_build)


@pytest.fixture
def tmp_dir(tmp_path):
    """Temporary directory for tests."""
    return tmp_path


@pytest.fixture
def tmp_repo(tmp_path):
    """Create a temporary git repository."""
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    # Initialize git repo
    import git
    repo = git.Repo.init(repo_dir)

    # Create a test file and commit
    test_file = repo_dir / "README.md"
    test_file.write_text("# Test Repository")

    repo.index.add([str(test_file)])
    repo.index.commit("Initial commit")

    # Create a tag
    repo.create_tag("test_tag")

    return repo_dir


@pytest.fixture
def mock_toolchain():
    """Mock toolchain for testing."""
    return ToolchainInfo(
        type="mock",
        version="1.0.0",
        path=Path("/mock/toolchain"),
        env_vars={"PATH": "/mock/toolchain/bin"},
        cross_compile_arm32="arm-mock-",
        cross_compile_arm64="aarch64-mock-",
        cross_compile_microblaze="microblazeel-xilinx-linux-gnu-",
    )


@pytest.fixture
def zynq_config_dict():
    """Zynq platform configuration dictionary."""
    return {
        "arch": "arm",
        "cross_compile": "arm-linux-gnueabihf-",
        "defconfig": "zynq_xcomm_adv7511_defconfig",
        "kernel_target": "uImage",
        "uimage_loadaddr": "0x8000",
        "dtb_path": "arch/arm/boot/dts",
        "kernel_image_path": "arch/arm/boot/uImage",
        "dtbs": [
            "zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb",
            "zynq-zc706-adv7511-ad9361-fmcomms2-3.dtb",
        ],
        "toolchain": {
            "preferred": "vivado",
            "fallback": ["arm", "system"],
        },
    }


@pytest.fixture
def zynqmp_config_dict():
    """ZynqMP platform configuration dictionary."""
    return {
        "arch": "arm64",
        "cross_compile": "aarch64-linux-gnu-",
        "defconfig": "adi_zynqmp_defconfig",
        "kernel_target": "Image",
        "dtb_path": "arch/arm64/boot/dts/xilinx",
        "kernel_image_path": "arch/arm64/boot/Image",
        "dtbs": [
            "zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb",
            "zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb",
        ],
        "toolchain": {
            "preferred": "vivado",
            "fallback": ["arm", "system"],
        },
    }


@pytest.fixture
def zynq_config(zynq_config_dict):
    """BuildConfig with Zynq configuration."""
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
            "zynq": zynq_config_dict,
        },
    }
    return BuildConfig.from_dict(config_data)


@pytest.fixture
def zynqmp_config(zynqmp_config_dict):
    """BuildConfig with ZynqMP configuration."""
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
            "zynqmp": zynqmp_config_dict,
        },
    }
    return BuildConfig.from_dict(config_data)


@pytest.fixture
def microblaze_config_dict():
    """MicroBlaze platform configuration dictionary."""
    return {
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


@pytest.fixture
def microblaze_config(microblaze_config_dict):
    """BuildConfig with MicroBlaze configuration."""
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
            "microblaze_vcu118": microblaze_config_dict,
        },
    }
    return BuildConfig.from_dict(config_data)


@pytest.fixture
def mock_kernel_source(tmp_path):
    """Create minimal kernel source structure."""
    kernel_dir = tmp_path / "linux"
    kernel_dir.mkdir()

    # Create basic structure
    (kernel_dir / "arch" / "arm" / "boot" / "dts").mkdir(parents=True)
    (kernel_dir / "arch" / "arm64" / "boot" / "dts" / "xilinx").mkdir(parents=True)
    (kernel_dir / "arch" / "microblaze" / "boot" / "dts").mkdir(parents=True)

    # Create dummy files
    (kernel_dir / "Makefile").write_text("# Dummy Makefile")
    (kernel_dir / ".config").write_text("# Config")

    # Create dummy kernel images
    (kernel_dir / "arch" / "arm" / "boot" / "uImage").write_text("dummy uImage")
    (kernel_dir / "arch" / "arm64" / "boot" / "Image").write_text("dummy Image")
    (kernel_dir / "arch" / "microblaze" / "boot" / "simpleImage.vcu118_ad9081").write_text("dummy simpleImage")

    # Create dummy DTBs
    (kernel_dir / "arch" / "arm" / "boot" / "dts" / "test.dtb").write_text("dummy dtb")
    (kernel_dir / "arch" / "arm64" / "boot" / "dts" / "xilinx" / "test.dtb").write_text("dummy dtb")

    return kernel_dir


@pytest.fixture
def mock_git_repo(mocker, tmp_path):
    """Mock GitRepository for testing."""
    mock_repo = MagicMock()
    mock_repo.local_path = tmp_path / "linux"
    mock_repo.clone.return_value = None
    mock_repo.fetch.return_value = None
    mock_repo.checkout.return_value = None
    mock_repo.get_commit_sha.return_value = "abc123def456"
    return mock_repo


@pytest.fixture
def mock_executor(mocker):
    """Mock BuildExecutor for testing."""
    from adibuild.core.executor import ExecutionResult

    mock_exec = MagicMock()

    # Create a successful result
    success_result = ExecutionResult(
        command="mock command",
        return_code=0,
        stdout="Success",
        stderr="",
        duration=1.0,
    )

    mock_exec.execute.return_value = success_result
    mock_exec.make.return_value = success_result
    mock_exec.check_tool.return_value = True
    mock_exec.check_tools.return_value = True

    return mock_exec
