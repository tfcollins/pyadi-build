"""Tests for the specialized download runner Docker environment."""

import os
from pathlib import Path
import pytest

def test_download_runner_artifacts_exist():
    """Verify that the Dockerfile and entrypoint script exist."""
    root = Path(__file__).parent.parent.parent
    docker_dir = root / "adibuild" / "docker" / "download_runner"
    
    dockerfile = docker_dir / "Dockerfile"
    entrypoint = docker_dir / "entrypoint.py"
    
    assert dockerfile.exists(), f"Dockerfile not found at {dockerfile}"
    assert entrypoint.exists(), f"Entrypoint script not found at {entrypoint}"

def test_docker_download_runner_orchestration(mocker):
    """Test the orchestration of the download runner container."""
    from adibuild.core.docker import DockerDownloadRunner
    
    mock_run = mocker.patch("subprocess.run")
    mock_run.return_value = mocker.Mock(returncode=0)
    
    # Mock existence and rename of downloaded file
    mocker.patch("pathlib.Path.exists", return_value=True)
    mocker.patch("pathlib.Path.rename")
    
    runner = DockerDownloadRunner()
    result = runner.download(
        version="2023.2",
        destination=Path("/tmp/vivado.bin"),
        credentials=mocker.Mock(username="user", password="pass")
    )
    
    assert result == Path("/tmp/vivado.bin")
    # Should call docker build and docker run
    assert mock_run.call_count >= 2
    
    # Verify build command
    build_call = mock_run.call_args_list[0]
    assert "build" in build_call.args[0]
    assert "adibuild/vivado-download-runner" in build_call.args[0]
    
    # Verify run command
    run_call = mock_run.call_args_list[1]
    assert "run" in run_call.args[0]
    assert "AMD_USERNAME=user" in run_call.args[0]
    assert "AMD_PASSWORD=pass" in run_call.args[0]
