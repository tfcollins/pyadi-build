"""CLI tests for boot-related build commands."""

from adibuild.cli.main import cli
from adibuild.core.config import BuildConfig


def _boot_config(project: str) -> BuildConfig:
    return BuildConfig.from_dict(
        {
            "project": project,
            "tag": "2023_R2",
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


def test_build_atf_docker_runner_is_forwarded(cli_runner, mocker):
    config = _boot_config("atf")
    platform_obj = mocker.Mock()
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=config)
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=platform_obj)
    builder_cls = mocker.patch("adibuild.cli.main.ATFBuilder")
    builder_cls.return_value.build.return_value = {"output_dir": "./build/atf"}

    result = cli_runner.invoke(
        cli,
        [
            "boot",
            "build-atf",
            "-p",
            "zynqmp",
            "--runner",
            "docker",
            "--docker-image",
            "custom/vivado:2023.2",
            "--tool-version",
            "2023.2",
        ],
    )

    assert result.exit_code == 0, result.output
    builder_cls.assert_called_once_with(
        config,
        platform_obj,
        runner="docker",
        docker_image="custom/vivado:2023.2",
        docker_tool_version="2023.2",
    )


def test_build_uboot_docker_runner_is_forwarded(cli_runner, mocker):
    config = _boot_config("uboot")
    platform_obj = mocker.Mock()
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=config)
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=platform_obj)
    builder_cls = mocker.patch("adibuild.cli.main.UBootBuilder")
    builder_cls.return_value.build.return_value = {"output_dir": "./build/uboot"}

    result = cli_runner.invoke(
        cli,
        [
            "boot",
            "build-uboot",
            "-p",
            "zynqmp",
            "--runner",
            "docker",
            "--docker-image",
            "custom/vivado:2023.2",
            "--tool-version",
            "2023.2",
        ],
    )

    assert result.exit_code == 0, result.output
    builder_cls.assert_called_once_with(
        config,
        platform_obj,
        runner="docker",
        docker_image="custom/vivado:2023.2",
        docker_tool_version="2023.2",
    )


def test_build_boot_docker_runner_defaults_image_from_tool_version(cli_runner, mocker):
    config = _boot_config("boot")
    platform_obj = mocker.Mock()
    mocker.patch("adibuild.cli.main.load_config_with_overrides", return_value=config)
    mocker.patch("adibuild.cli.main.get_platform_instance", return_value=platform_obj)
    builder_cls = mocker.patch("adibuild.cli.main.BootBuilder")
    builder_cls.return_value.build.return_value = {"boot_bin": "./build/BOOT.BIN"}

    result = cli_runner.invoke(
        cli,
        [
            "boot",
            "build-boot",
            "-p",
            "zynqmp",
            "--runner",
            "docker",
            "--tool-version",
            "2023.2",
        ],
    )

    assert result.exit_code == 0, result.output
    builder_cls.assert_called_once_with(
        config,
        platform_obj,
        script_mode=False,
        runner="docker",
        docker_image="adibuild/vivado:2023.2",
        docker_tool_version="2023.2",
    )


def test_build_boot_generate_script_with_docker_runner(cli_runner, tmp_path, mocker):
    mocker.patch("pathlib.Path.home", return_value=tmp_path)
    config_file = tmp_path / "boot.yaml"
    config_file.write_text("""
project: boot
tag: 2023_R2
build:
  output_dir: ./build
platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    kernel_target: Image
    tool_version: 2023.2
boot:
  xsa_path: /tmp/test.xsa
  fsbl_path: /tmp/fsbl.elf
  pmufw_path: /tmp/pmufw.elf
  atf_path: /tmp/bl31.elf
  uboot_path: /tmp/u-boot.elf
""")

    result = cli_runner.invoke(
        cli,
        [
            "--config",
            str(config_file),
            "boot",
            "build-boot",
            "-p",
            "zynqmp",
            "--generate-script",
            "--runner",
            "docker",
            "--docker-image",
            "custom/vivado:2023.2",
        ],
    )

    assert result.exit_code == 0, result.output
    script_file = tmp_path / ".adibuild" / "work" / "build_boot_arm64.sh"
    content = script_file.read_text()
    assert "docker run --rm" in content
    assert "custom/vivado:2023.2" in content
