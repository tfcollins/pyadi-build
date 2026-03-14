from __future__ import annotations

import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from adibuild.core.vivado import VivadoInstaller

"""Real Docker-backed Vivado installation test."""

# Use a specific version for testing to avoid issues with latest
# This version must be one that's available for automated download
VIVADO_TEST_VERSION = "2023.2"


@pytest.fixture(scope="module")
def repo_root():
    """Get the repository root path."""
    return Path(__file__).parent.parent.parent.resolve()


@pytest.fixture(scope="module")
def docker_vivado_test_install_version():
    """Version of Vivado to install in Docker for tests."""
    return os.environ.get("ADIBUILD_DOCKER_VIVADO_VERSION", VIVADO_TEST_VERSION)


@pytest.mark.real_build
@pytest.mark.vivado_docker
def test_real_vivado_docker_install(
    tmp_path, repo_root, docker_vivado_test_install_version
):
    """
    Test a real Vivado installation into a Docker image.
    This test is slow and requires AMD credentials.
    """
    if not os.environ.get("AMD_USERNAME") or not os.environ.get("AMD_PASSWORD"):
        pytest.skip("AMD_USERNAME and AMD_PASSWORD environment variables not set")

    if not shutil.which("docker"):
        pytest.skip("Docker not found in PATH")

    # Use a clean workspace
    workspace = tmp_path / "vivado_docker_install"
    workspace.mkdir()

    # Create a dummy project structure if needed or just use current
    # For now we'll just test that the image builds correctly

    from adibuild.core.docker import VivadoDockerImageManager

    manager = VivadoDockerImageManager(work_dir=workspace)

    # We want to test the full flow including the download inside the container
    # To do this without actually downloading ~100GB every time,
    # we can mock the download strategy or use a small version if available.
    # But this is 'real' integration test.

    try:
        # Build the image - this will trigger the download runner
        image_tag = f"adibuild-test-vivado:{uuid.uuid4().hex[:8]}"
        manager.build_image(
            version=docker_vivado_test_install_version,
            tag=image_tag,
            # Pass credentials through environment
        )

        # Verify the image exists and has vivado
        # We can run a simple command in the image
        cmd = ["docker", "run", "--rm", image_tag, "vivado", "-version"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        assert (
            f"Vivado v{docker_vivado_test_install_version}" in result.stdout
            or docker_vivado_test_install_version in result.stdout
        )

    finally:
        # Cleanup the test image
        if "image_tag" in locals():
            subprocess.run(["docker", "rmi", image_tag], capture_output=True)


@pytest.mark.real_build
@pytest.mark.vivado_docker
def test_download_runner_orchestration_manual(
    tmp_path, repo_root, docker_vivado_test_install_version
):
    """
    Test the download runner orchestration logic specifically.
    """
    if not os.environ.get("AMD_USERNAME") or not os.environ.get("AMD_PASSWORD"):
        pytest.skip("AMD_USERNAME and AMD_PASSWORD environment variables not set")

    from adibuild.core.vivado import VivadoInstaller

    installer = VivadoInstaller()
    installer.resolve_release(docker_vivado_test_install_version)

    # We don't want to actually run the full download here if we can avoid it
    # But we want to test that the container starts and tries to download.

    # We can use a trick: provide invalid credentials and see if it fails as expected
    # OR provide a very small timeout.

    from adibuild.core.docker import build_download_runner_image

    # 1. Build the runner image
    runner_image = build_download_runner_image()

    # 2. Try to run it with a very short timeout or invalid setup
    # Actually, let's just verify it builds and can be started.

    container_name = f"adibuild-test-runner-{uuid.uuid4().hex[:8]}"
    try:
        cmd = [
            "docker",
            "run",
            "--name",
            container_name,
            "-d",
            "-e",
            "AMD_USERNAME=invalid",
            "-e",
            "AMD_PASSWORD=invalid",
            "-e",
            f"VIVADO_INSTALL_VERSION={docker_vivado_test_install_version}",
            "-e",
            f"ADIBUILD_BROWSER_HEADLESS={os.environ.get('ADIBUILD_BROWSER_HEADLESS', '1')}",
            "-v",
            f"{repo_root}:/src:ro",
            runner_image,
        ]

        subprocess.run(cmd, check=True)

        # Check logs after a few seconds
        import time

        time.sleep(5)
        logs = subprocess.run(
            ["docker", "logs", container_name], capture_output=True, text=True
        ).stdout

        # It should have started and attempted to load the strategy
        assert "Starting Vivado download runner" in logs

    finally:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


@pytest.mark.real_build
@pytest.mark.vivado_browser
def test_browser_download_strategy_manual():
    """
    Directly test the browser download strategy if possible.
    """
    if not os.environ.get("AMD_USERNAME") or not os.environ.get("AMD_PASSWORD"):
        pytest.skip("AMD_USERNAME and AMD_PASSWORD environment variables not set")

    from importlib.util import find_spec

    if not find_spec("playwright"):
        pytest.skip("playwright not installed on host")

    from adibuild.core.vivado import PlaywrightDownloadStrategy, VivadoCredentials

    strategy = PlaywrightDownloadStrategy()
    installer = VivadoInstaller()
    release = installer.resolve_release(VIVADO_TEST_VERSION)
    credentials = VivadoCredentials.from_env()

    # We only test login and cookie extraction, not full 100GB download
    try:
        cookies = strategy.authenticate(release, credentials)
        assert cookies
        assert any("xilinx" in c.get("domain", "").lower() for c in cookies)
    except Exception as e:
        pytest.fail(f"Browser authentication failed: {e}")


@pytest.mark.real_build
@pytest.mark.vivado_stealth
def test_stealth_browser_download_strategy_manual():
    """
    Directly test the stealth browser download strategy.
    """
    if not os.environ.get("AMD_USERNAME") or not os.environ.get("AMD_PASSWORD"):
        pytest.skip("AMD_USERNAME and AMD_PASSWORD environment variables not set")

    from importlib.util import find_spec

    if not find_spec("playwright") or not find_spec("playwright_stealth"):
        pytest.skip("playwright or playwright-stealth not installed on host")

    from adibuild.core.vivado import PlaywrightStealthDownloadStrategy, VivadoCredentials

    strategy = PlaywrightStealthDownloadStrategy()
    installer = VivadoInstaller()
    release = installer.resolve_release(VIVADO_TEST_VERSION)
    credentials = VivadoCredentials.from_env()

    try:
        cookies = strategy.authenticate(release, credentials)
        assert cookies
    except Exception as e:
        pytest.fail(f"Stealth browser authentication failed: {e}")
