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
