from adibuild.cli.main import cli


def test_generate_script_zynqmp(cli_runner, tmp_path, mocker):
    """Test generating a build script for ZynqMP."""

    # Mock home directory to use tmp_path
    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Run the build command with --generate-script
    result = cli_runner.invoke(
        cli, ["linux", "build", "-p", "zynqmp", "-t", "2023_R2", "--generate-script"]
    )

    assert result.exit_code == 0, f"Command failed: {result.output}"

    # Verify script file exists
    # The default work dir is ~/.adibuild/work
    work_dir = tmp_path / ".adibuild" / "work"
    # Note: ZynqMP arch is arm64
    script_file = work_dir / "build_linux_arm64.sh"

    assert script_file.exists()

    content = script_file.read_text()

    # Verify content contains expected commands
    assert "#!/bin/bash" in content
    assert "git clone" in content
    # Environment variables are exported
    assert "export ARCH='arm64'" in content
    assert "make adi_zynqmp_defconfig" in content

    # Check output
    assert "Generating build script" in result.output


def test_generate_script_microblaze(cli_runner, tmp_path, mocker):
    """Test generating a build script for MicroBlaze."""

    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    result = cli_runner.invoke(cli, ["linux", "build", "-p", "microblaze", "--generate-script"])

    assert result.exit_code == 0

    work_dir = tmp_path / ".adibuild" / "work"
    script_file = work_dir / "build_linux_microblaze.sh"

    assert script_file.exists()
    content = script_file.read_text()

    # Check for MicroBlaze specific commands
    assert "simpleImage" in content
    # Check for rootfs download
    assert "wget" in content or "curl" in content
    assert "rootfs.cpio.gz" in content


def test_generate_script_with_custom_config(cli_runner, tmp_path, mocker):
    """Test generating script with custom config file."""

    mocker.patch("pathlib.Path.home", return_value=tmp_path)

    # Create a dummy config file
    config_file = tmp_path / "custom_config"
    config_file.write_text("CONFIG_TEST=y")

    result = cli_runner.invoke(
        cli, ["linux", "build", "-p", "zynq", "--defconfig", str(config_file), "--generate-script"]
    )

    assert result.exit_code == 0

    work_dir = tmp_path / ".adibuild" / "work"
    # Note: Zynq arch is arm
    script_file = work_dir / "build_linux_arm.sh"

    content = script_file.read_text()

    # CLI --defconfig updates the make target
    assert f"make {config_file}" in content

    # Check for cp command for artifacts
    assert "cp" in content
    assert "uImage" in content
