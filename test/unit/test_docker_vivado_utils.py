"""Tests for Docker Vivado integration test helpers."""

from test.integration import docker_utils


def test_docker_vivado_version_defaults(monkeypatch):
    monkeypatch.delenv("ADIBUILD_VIVADO_DOCKER_VERSION", raising=False)

    assert docker_utils.docker_vivado_version() == "2023.2"


def test_docker_vivado_version_uses_env(monkeypatch):
    monkeypatch.setenv("ADIBUILD_VIVADO_DOCKER_VERSION", "2025.1")

    assert docker_utils.docker_vivado_version() == "2025.1"


def test_docker_vivado_install_version_uses_release_mapping():
    assert docker_utils.docker_vivado_install_version("2025.1") == "2025.1"


def test_keep_docker_vivado_artifacts_defaults_false(monkeypatch):
    monkeypatch.delenv("ADIBUILD_KEEP_VIVADO_DOCKER_ARTIFACTS", raising=False)

    assert docker_utils.keep_docker_vivado_artifacts() is False


def test_keep_docker_vivado_artifacts_honors_truthy_env(monkeypatch):
    monkeypatch.setenv("ADIBUILD_KEEP_VIVADO_DOCKER_ARTIFACTS", "true")

    assert docker_utils.keep_docker_vivado_artifacts() is True


def test_docker_vivado_cache_dir_defaults_under_tmp(monkeypatch, tmp_path):
    monkeypatch.delenv("ADIBUILD_VIVADO_DOCKER_CACHE_DIR", raising=False)

    assert (
        docker_utils.docker_vivado_cache_dir(tmp_path) == tmp_path / "vivado-docker-cache"
    )


def test_docker_vivado_cache_dir_uses_env(monkeypatch, tmp_path):
    configured = tmp_path / "shared-cache"
    monkeypatch.setenv("ADIBUILD_VIVADO_DOCKER_CACHE_DIR", str(configured))

    assert docker_utils.docker_vivado_cache_dir(tmp_path) == configured
