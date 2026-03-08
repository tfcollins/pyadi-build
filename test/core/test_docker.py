from pathlib import Path

import pytest

from adibuild.core.config import BuildConfig
from adibuild.core.docker import (
    DockerExecutionConfig,
    DockerMount,
    VivadoDockerImageManager,
    build_docker_execution_config,
    container_vivado_toolchain,
    default_vivado_image_tag,
)
from adibuild.core.executor import BuildError, BuildExecutor, ScriptBuilder
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.atf import ATFBuilder


def test_default_vivado_image_tag():
    assert default_vivado_image_tag("2023.2") == "adibuild/vivado:2023.2"


def test_container_vivado_toolchain_uses_release_mapping():
    toolchain = container_vivado_toolchain("2025.1")

    assert toolchain.type == "vivado"
    assert toolchain.version == "2025.1"
    assert toolchain.path == Path("/opt/Xilinx/Vivado/2025.1")
    assert toolchain.cross_compile_arm64 == "aarch64-linux-gnu-"


def test_build_docker_execution_config_collects_workspace_and_cache(tmp_path, mocker):
    home = tmp_path / "home"
    workspace = tmp_path / "repo"
    workspace.mkdir(parents=True)
    (home / ".adibuild").mkdir(parents=True)
    hw_dir = tmp_path / "artifacts"
    hw_dir.mkdir()
    hw_file = hw_dir / "system.xsa"
    hw_file.write_text("xsa")

    mocker.patch("pathlib.Path.home", return_value=home)

    config = {
        "build": {"output_dir": "./build"},
        "boot": {"xsa_path": str(hw_file)},
    }
    docker_config = build_docker_execution_config(
        config,
        image="adibuild/vivado:2023.2",
        tool_version="2023.2",
        work_dir=home / ".adibuild" / "work",
        cwd=workspace,
    )

    mounted_sources = {mount.source for mount in docker_config.mounts}
    assert workspace.resolve() in mounted_sources
    assert (home / ".adibuild").resolve() in mounted_sources
    assert hw_dir.resolve() in mounted_sources


def test_executor_writes_docker_script(tmp_path):
    script_path = tmp_path / "build.sh"
    executor = BuildExecutor(
        script_builder=ScriptBuilder(script_path),
        docker_config=DockerExecutionConfig(
            image="custom/vivado:2023.2",
            tool_version="2023.2",
            mounts=(
                DockerMount(source=tmp_path, target=tmp_path),
                DockerMount(source=Path("/tmp"), target=Path("/tmp")),
            ),
            workdir=tmp_path,
            home_dir=Path("/tmp/adibuild-home"),
            user="1000:1000",
        ),
    )

    executor.execute(["make", "-j4"], env={"ARCH": "arm"})

    content = script_path.read_text()
    assert "docker run --rm" in content
    assert "custom/vivado:2023.2" in content
    assert "/opt/Xilinx/Vivado/2023.2/settings64.sh" in content
    assert "-e ARCH=arm" in content


def test_vivado_docker_image_manager_builds_image(tmp_path, mocker):
    installer = mocker.Mock()
    installer.cache_dir = tmp_path / "cache"
    installer.resolve_release.return_value = mocker.Mock(
        version="2023.2",
        install_version="2023.2",
    )
    manager = VivadoDockerImageManager(cache_dir=tmp_path / "cache", installer=installer)

    mock_run = mocker.patch("subprocess.run")
    result = manager.build_image("2023.2")

    installer.install.assert_called_once()
    build_call = mock_run.call_args_list[-1]
    assert build_call.args[0][:3] == ["docker", "build", "-t"]
    assert result["tag"] == "adibuild/vivado:2023.2"


def test_platform_get_toolchain_uses_container_vivado_toolchain(mocker):
    platform = ZynqMPPlatform(
        {
            "arch": "arm64",
            "cross_compile": "aarch64-linux-gnu-",
            "kernel_target": "Image",
            "_runner": "docker",
            "_docker_tool_version": "2023.2",
        }
    )
    select_toolchain = mocker.patch("adibuild.platforms.base.select_toolchain")

    toolchain = platform.get_toolchain()

    assert toolchain.type == "vivado"
    assert toolchain.version == "2023.2"
    assert toolchain.path == Path("/opt/Xilinx/Vivado/2023.2")
    select_toolchain.assert_not_called()


def test_builder_validate_environment_requires_host_docker(mocker):
    config = BuildConfig.from_dict(
        {
            "project": "atf",
            "build": {"output_dir": "./build"},
            "platforms": {
                "zynqmp": {
                    "arch": "arm64",
                    "cross_compile": "aarch64-linux-gnu-",
                    "kernel_target": "Image",
                    "tool_version": "2023.2",
                }
            },
        }
    )
    platform = ZynqMPPlatform(
        {
            "arch": "arm64",
            "cross_compile": "aarch64-linux-gnu-",
            "kernel_target": "Image",
            "tool_version": "2023.2",
        }
    )
    builder = ATFBuilder(
        config,
        platform,
        runner="docker",
        docker_image="custom/vivado:2023.2",
        docker_tool_version="2023.2",
    )
    mocker.patch("shutil.which", return_value=None)

    with pytest.raises(BuildError, match="docker"):
        builder.validate_environment()
