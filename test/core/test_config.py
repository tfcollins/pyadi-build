"""Tests for configuration management."""

import json
from pathlib import Path

import pytest
import yaml

from adibuild.core.config import BuildConfig, ConfigurationError


def test_build_config_from_dict():
    """Test creating BuildConfig from dictionary."""
    data = {"project": "linux", "platforms": {"zynq": {"arch": "arm"}}}
    config = BuildConfig.from_dict(data)

    assert config.get("project") == "linux"
    assert config.get("platforms.zynq.arch") == "arm"


def test_build_config_from_yaml(tmp_path):
    """Test loading BuildConfig from YAML file."""
    config_file = tmp_path / "config.yaml"
    data = {"project": "linux", "tag": "2023_R2"}

    with open(config_file, "w") as f:
        yaml.dump(data, f)

    config = BuildConfig.from_yaml(config_file)
    assert config.get("project") == "linux"
    assert config.get("tag") == "2023_R2"


def test_build_config_from_json(tmp_path):
    """Test loading BuildConfig from JSON file."""
    config_file = tmp_path / "config.json"
    data = {"project": "linux", "tag": "2023_R2"}

    with open(config_file, "w") as f:
        json.dump(data, f)

    config = BuildConfig.from_json(config_file)
    assert config.get("project") == "linux"
    assert config.get("tag") == "2023_R2"


def test_build_config_not_found():
    """Test error when config file not found."""
    with pytest.raises(ConfigurationError):
        BuildConfig.from_yaml("/nonexistent/config.yaml")


def test_build_config_get_with_default():
    """Test getting values with defaults."""
    config = BuildConfig.from_dict({"project": "linux"})

    assert config.get("project") == "linux"
    assert config.get("nonexistent", "default") == "default"
    assert config.get("nested.key", 42) == 42


def test_build_config_dot_notation():
    """Test dot notation access."""
    data = {
        "build": {
            "parallel_jobs": 8,
            "output_dir": "./build",
        }
    }
    config = BuildConfig.from_dict(data)

    assert config.get("build.parallel_jobs") == 8
    assert config.get("build.output_dir") == "./build"


def test_build_config_set():
    """Test setting configuration values."""
    config = BuildConfig.from_dict({})

    config.set("project", "linux")
    config.set("build.parallel_jobs", 16)

    assert config.get("project") == "linux"
    assert config.get("build.parallel_jobs") == 16


def test_build_config_deep_merge():
    """Test deep merging of configurations."""
    base = {
        "project": "linux",
        "build": {"parallel_jobs": 4, "clean_before": False},
    }
    override = {
        "build": {"parallel_jobs": 8},
        "tag": "2023_R2",
    }

    merged = BuildConfig._deep_merge(base, override)

    assert merged["project"] == "linux"
    assert merged["build"]["parallel_jobs"] == 8
    assert merged["build"]["clean_before"] is False
    assert merged["tag"] == "2023_R2"


def test_build_config_get_platform(zynq_config):
    """Test getting platform configuration."""
    platform = zynq_config.get_platform("zynq")

    assert platform["arch"] == "arm"
    assert platform["defconfig"] == "zynq_xcomm_adv7511_defconfig"


def test_build_config_get_platform_not_found(zynq_config):
    """Test error when platform not found."""
    with pytest.raises(ConfigurationError):
        zynq_config.get_platform("nonexistent")


def test_build_config_get_project(zynq_config):
    """Test getting project name."""
    assert zynq_config.get_project() == "linux"


def test_build_config_get_repository(zynq_config):
    """Test getting repository URL."""
    repo = zynq_config.get_repository()
    assert "github.com" in repo
    assert "linux" in repo


def test_build_config_get_tag(zynq_config):
    """Test getting git tag."""
    assert zynq_config.get_tag() == "2023_R2"


def test_build_config_get_parallel_jobs(zynq_config):
    """Test getting parallel jobs with default."""
    assert zynq_config.get_parallel_jobs() == 4

    config = BuildConfig.from_dict({})
    assert config.get_parallel_jobs(default=8) == 8


def test_build_config_to_yaml(tmp_path, zynq_config):
    """Test saving configuration to YAML."""
    output_file = tmp_path / "output.yaml"
    zynq_config.to_yaml(output_file)

    assert output_file.exists()

    # Load and verify
    loaded = BuildConfig.from_yaml(output_file)
    assert loaded.get("project") == "linux"


def test_build_config_to_json(tmp_path, zynq_config):
    """Test saving configuration to JSON."""
    output_file = tmp_path / "output.json"
    zynq_config.to_json(output_file)

    assert output_file.exists()

    # Load and verify
    loaded = BuildConfig.from_json(output_file)
    assert loaded.get("project") == "linux"
