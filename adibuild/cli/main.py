"""Command-line interface for adibuild."""

import json
import logging
from pathlib import Path
from typing import Any

import click

from adibuild.cli.helpers import (
    create_default_config,
    display_build_summary,
    display_platforms,
    display_toolchain_info,
    get_platform_instance,
    load_config_with_overrides,
    print_error,
    print_success,
    print_version,
    tag_to_tool_version,
    validate_config_file,
)
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.boot import BootBuilder
from adibuild.projects.genalyzer import GenalyzerBuilder
from adibuild.projects.hdl import HDLBuilder
from adibuild.projects.iio_emu import IIOEmuBuilder
from adibuild.projects.libad9361 import LibAD9361Builder
from adibuild.projects.libtinyiiod import LibTinyIIODBuilder
from adibuild.projects.linux import LinuxBuilder
from adibuild.projects.noos import NoOSBuilder
from adibuild.projects.uboot import UBootBuilder
from adibuild.utils.logger import setup_logging


def _load_vivado_credentials(non_interactive: bool):
    """Load AMD credentials from env vars or interactive prompt."""
    from adibuild.core.vivado import VivadoCredentials

    creds = VivadoCredentials.from_env()
    if creds or non_interactive:
        return creds

    username = click.prompt("AMD account username", type=str)
    password = click.prompt("AMD account password", type=str, hide_input=True)
    if not username or not password:
        return None
    return VivadoCredentials(username=username, password=password)


def _resolve_docker_runner(
    config: BuildConfig,
    platform_config: dict[str, Any] | None,
    runner: str | None,
    docker_image: str | None,
    tool_version: str | None,
    tag: str | None,
) -> tuple[str, str | None, str | None]:
    """Resolve runner/image/tool-version settings from CLI and config."""
    from adibuild.core.docker import default_vivado_image_tag

    resolved_runner = runner or config.get("build.runner", "local")
    resolved_image = docker_image or config.get("build.docker.image")
    resolved_tool_version = (
        tool_version
        or (platform_config or {}).get("tool_version")
        or config.get("build.docker.tool_version")
    )

    if not resolved_tool_version:
        # tag_to_tool_version expects a str, so only call if tag or config.get_tag() is not None
        current_tag = tag or config.get_tag()
        if current_tag:
            resolved_tool_version = tag_to_tool_version(current_tag)

    if resolved_runner == "docker":
        if not resolved_tool_version:
            raise click.ClickException(
                "Docker runner requires a Vivado tool version. "
                "Use --tool-version, set build.docker.tool_version, or use a release tag like 2023_R2."
            )
        resolved_image = resolved_image or default_vivado_image_tag(resolved_tool_version)

    return resolved_runner, resolved_image, resolved_tool_version


# Global options
@click.group()
@click.option(
    "--version",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: (print_version(), ctx.exit(0)) if value else None,
    help="Show version and exit",
)
@click.option(
    "--verbose",
    "-v",
    count=True,
    help="Increase verbosity (can be used multiple times)",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.pass_context
def cli(ctx, verbose, config):
    """
    adibuild - Build system for ADI projects.

    Build Linux kernels, HDL projects, and libiio for Analog Devices platforms.
    """
    ctx.ensure_object(dict)

    # Setup logging based on verbosity
    if verbose == 0:
        log_level = logging.WARNING
    elif verbose == 1:
        log_level = logging.INFO
    else:
        log_level = logging.DEBUG

    setup_logging(level=log_level)

    # Store config path in context
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


@cli.group()
def hdl():
    """HDL project build commands."""
    pass


@hdl.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=False,
    help="Target platform/build config (e.g. zed_fmcomms2)",
)
@click.option("--project", help="HDL project name (e.g. fmcomms2)")
@click.option("--carrier", help="Carrier board name (e.g. zed)")
@click.option("--arch", default="unknown", help="Architecture (e.g. arm, arm64)")
@click.option("--tag", "-t", help="Git tag or branch to build")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option("--ignore-version-check", is_flag=True, help="Ignore Vivado version check")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Generate bash script instead of executing build",
)
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override Vivado version (e.g., 2023.2). Auto-detected from tag if not specified.",
)
@click.option(
    "--runner",
    type=click.Choice(["local", "docker"]),
    help="Execution backend for the build",
)
@click.option("--docker-image", help="Reusable Docker image tag for --runner docker")
@click.pass_context
def build_hdl(
    ctx,
    platform,
    project,
    carrier,
    arch,
    tag,
    output,
    clean,
    jobs,
    ignore_version_check,
    generate_script,
    tool_version,
    runner,
    docker_image,
):
    """
    Build HDL project for specified platform.

    You must specify either --platform OR both --project and --carrier.

    Examples:

        adibuild hdl build -p zed_fmcomms2

        adibuild hdl build --project fmcomms2 --carrier zed

        adibuild hdl build --project daq2 --carrier zcu102 --arch arm64
    """
    if not platform and not (project and carrier):
        print_error("You must specify either --platform OR both --project and --carrier")

    if platform and (project or carrier):
        # We could allow overriding, but keeping it simple for now
        print_error("Specify --platform OR --project/--carrier, not both")

    # Derive tool version from tag if not explicitly specified
    if not tool_version and tag:
        tool_version = tag_to_tool_version(tag)
        if tool_version:
            click.echo(f"Auto-detected tool version {tool_version} from tag {tag}")

    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="hdl",
        )

        # Handle dynamic platform injection
        if not platform:
            platform = f"{carrier}_{project}"
            # Inject config for this synthetic platform
            platform_config = {
                "hdl_project": project,
                "carrier": carrier,
                "arch": arch,
                # Add "name" so it's available in platform object (used by HDLPlatform.name)
                "name": platform,
            }
            if tool_version:
                platform_config["tool_version"] = tool_version
            config.set(f"platforms.{platform}", platform_config)
        elif tool_version:
            # Set tool_version in existing platform config
            platform_config = config.get_platform(platform)
            platform_config["tool_version"] = tool_version
            config.set(f"platforms.{platform}", platform_config)

        # Override parallel jobs if specified
        if jobs:
            config.set("build.parallel_jobs", jobs)

        # Override output directory if specified
        if output:
            config.set("build.output_dir", output)

        platform_config = config.get_platform(platform)
        resolved_runner, resolved_image, resolved_tool_version = _resolve_docker_runner(
            config,
            platform_config,
            runner,
            docker_image,
            tool_version,
            tag,
        )

        # Get platform instance
        # Note: HDL platforms might just use generic Platform class
        # or we might need specific ones if toolchain logic differs.
        # For now, generic Platform with config dict is enough.
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = HDLBuilder(
            config,
            platform_obj,
            script_mode=generate_script,
            runner=resolved_runner,
            docker_image=resolved_image,
            docker_tool_version=resolved_tool_version,
        )

        # Execute build
        result = builder.build(
            clean_before=clean, ignore_version_check=ignore_version_check
        )

        # Display summary (reuse or create new)
        # display_build_summary is tailored for Linux (dtbs etc), but we can adapt it or make generic
        # For now, just print success.
        print_success(f"HDL Build completed. Artifacts in: {result['output_dir']}")

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if ctx.obj.get("verbose", 0) > 1:
            import traceback

            traceback.print_exc()


# no-OS command group
@cli.group()
def noos():
    """no-OS bare-metal firmware build commands."""
    pass


@noos.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config (e.g. xilinx_ad9081)",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option(
    "--hardware-file",
    "hardware_file",
    type=click.Path(),
    help="Path to hardware file (.xsa for Xilinx, .ioc for STM32)",
)
@click.option("--profile", help="Hardware profile (e.g., vcu118_ad9081_m8_l4)")
@click.option("--iiod", is_flag=True, default=None, help="Enable IIO daemon (IIOD=y)")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Generate bash script instead of executing build",
)
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override Vivado version (e.g., 2023.2). Auto-detected from tag if not specified.",
)
@click.option(
    "--runner",
    type=click.Choice(["local", "docker"]),
    help="Execution backend for the build",
)
@click.option("--docker-image", help="Reusable Docker image tag for --runner docker")
@click.pass_context
def build_noos(
    ctx,
    platform,
    tag,
    hardware_file,
    profile,
    iiod,
    clean,
    jobs,
    generate_script,
    tool_version,
    runner,
    docker_image,
):
    """
    Build no-OS bare-metal firmware for specified platform.

    Examples:

        adibuild noos build -p xilinx_ad9081

        adibuild noos build -p stm32_ad9081 --hardware-file project.ioc

        adibuild noos build -p xilinx_ad9081 --generate-script
    """
    # Derive tool version from tag if not explicitly specified
    if not tool_version and tag:
        tool_version = tag_to_tool_version(tag)
        if tool_version:
            click.echo(f"Auto-detected tool version {tool_version} from tag {tag}")

    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="noos",
        )

        # Apply CLI overrides to platform config
        platform_config = config.get_platform(platform)

        if hardware_file:
            platform_config["hardware_file"] = hardware_file

        if profile:
            platform_config["profile"] = profile

        if iiod is not None:
            platform_config["iiod"] = iiod

        if tool_version:
            platform_config["tool_version"] = tool_version

        config.set(f"platforms.{platform}", platform_config)

        # Override parallel jobs if specified
        if jobs:
            config.set("build.parallel_jobs", jobs)

        resolved_runner, resolved_image, resolved_tool_version = _resolve_docker_runner(
            config,
            platform_config,
            runner,
            docker_image,
            tool_version,
            tag,
        )

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = NoOSBuilder(
            config,
            platform_obj,
            script_mode=generate_script,
            runner=resolved_runner,
            docker_image=resolved_image,
            docker_tool_version=resolved_tool_version,
        )

        # Execute build
        result = builder.build(clean_before=clean)

        print_success(f"no-OS Build completed. Artifacts in: {result['output_dir']}")

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if ctx.obj.get("verbose", 0) > 1:
            import traceback

            traceback.print_exc()


@noos.command(name="clean")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--deep", is_flag=True, help="Use 'reset' target instead of 'clean'")
@click.pass_context
def clean_noos(ctx, platform, tag, deep):
    """
    Clean no-OS build artifacts.

    By default uses 'make clean'. Use --deep for 'make reset'.
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="noos",
        )

        platform_obj = get_platform_instance(config, platform)
        builder = NoOSBuilder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# libad9361-iio command group
@cli.group()
def libad9361():
    """libad9361-iio library build commands."""
    pass


@libad9361.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config (e.g. arm, arm64, native)",
)
@click.option("--tag", "-t", help="Git tag or branch (e.g. main, 2023_R2)")
@click.option(
    "--arch",
    type=click.Choice(["arm", "arm64", "native"], case_sensitive=False),
    help="Target architecture (overrides config)",
)
@click.option(
    "--cross-compile",
    help="Cross-compiler prefix override (e.g. arm-linux-gnueabihf-)",
)
@click.option(
    "--libiio-path",
    type=click.Path(),
    help="Path to cross-compiled libiio (must contain include/ and lib/)",
)
@click.option("--clean", is_flag=True, help="Remove build directory before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel make jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Write a bash build script instead of building",
)
@click.pass_context
def build_libad9361(
    ctx, platform, tag, arch, cross_compile, libiio_path, clean, jobs, generate_script
):
    """
    Build the libad9361-iio shared library.

    Clones https://github.com/analogdevicesinc/libad9361-iio, configures
    it with CMake, and builds a shared library for the target architecture.

    Example:

        adibuild --config configs/libad9361/default.yaml libad9361 build -p arm
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="libad9361",
        )

        platform_obj = get_platform_instance(config, platform)

        # Apply CLI overrides to platform config
        if arch:
            platform_obj.config["arch"] = arch
        if cross_compile:
            platform_obj.config["cross_compile"] = cross_compile
        if libiio_path:
            platform_obj.config["libiio_path"] = libiio_path

        builder = LibAD9361Builder(config, platform_obj, script_mode=generate_script)
        result = builder.build(clean_before=clean, jobs=jobs)

        if generate_script:
            print_success(
                f"Build script written to {result.get('script', 'build script')}"
            )
        else:
            print_success(
                f"libad9361-iio built successfully. "
                f"{len(result.get('artifacts', []))} artifact(s) in "
                f"{result.get('output_dir', '')}"
            )

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@libad9361.command(name="clean")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option(
    "--deep",
    is_flag=True,
    help="Remove entire build directory (default: make clean)",
)
@click.pass_context
def clean_libad9361(ctx, platform, tag, deep):
    """
    Clean libad9361-iio build artifacts.

    By default runs ``make clean`` inside the build directory.
    Use --deep to remove the entire build directory tree.
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="libad9361",
        )

        platform_obj = get_platform_instance(config, platform)
        builder = LibAD9361Builder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# libtinyiiod command group
@cli.group()
def libtinyiiod():
    """libtinyiiod library build commands."""
    pass


@libtinyiiod.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config (e.g. arm, arm64, native)",
)
@click.option("--tag", "-t", help="Git tag or branch (e.g. main, 2023_R2)")
@click.option(
    "--arch",
    type=click.Choice(["arm", "arm64", "native"], case_sensitive=False),
    help="Target architecture (overrides config)",
)
@click.option(
    "--cross-compile",
    help="Cross-compiler prefix override (e.g. arm-linux-gnueabihf-)",
)
@click.option("--clean", is_flag=True, help="Remove build directory before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel make jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Write a bash build script instead of building",
)
@click.pass_context
def build_libtinyiiod(
    ctx, platform, tag, arch, cross_compile, clean, jobs, generate_script
):
    """
    Build the libtinyiiod shared library.

    Clones https://github.com/analogdevicesinc/libtinyiiod, configures
    it with CMake, and builds a shared library for the target architecture.

    Example:

        adibuild --config configs/libtinyiiod/default.yaml libtinyiiod build -p arm
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="libtinyiiod",
        )

        platform_obj = get_platform_instance(config, platform)

        # Apply CLI overrides to platform config
        if arch:
            platform_obj.config["arch"] = arch
        if cross_compile:
            platform_obj.config["cross_compile"] = cross_compile

        builder = LibTinyIIODBuilder(config, platform_obj, script_mode=generate_script)
        result = builder.build(clean_before=clean, jobs=jobs)

        if generate_script:
            print_success(
                f"Build script written to {result.get('script', 'build script')}"
            )
        else:
            print_success(
                f"libtinyiiod built successfully. "
                f"{len(result.get('artifacts', []))} artifact(s) in "
                f"{result.get('output_dir', '')}"
            )

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@libtinyiiod.command(name="clean")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option(
    "--deep",
    is_flag=True,
    help="Remove entire build directory (default: make clean)",
)
@click.pass_context
def clean_libtinyiiod(ctx, platform, tag, deep):
    """
    Clean libtinyiiod build artifacts.

    By default runs ``make clean`` inside the build directory.
    Use --deep to remove the entire build directory tree.
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="libtinyiiod",
        )

        platform_obj = get_platform_instance(config, platform)
        builder = LibTinyIIODBuilder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# iio-emu command group
@cli.group(name="iio-emu")
def iio_emu():
    """iio-emu server application build commands."""
    pass


@iio_emu.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config (e.g. arm, arm64, native)",
)
@click.option("--tag", "-t", help="Git tag or branch (e.g. main, v0.1.0)")
@click.option(
    "--arch",
    type=click.Choice(["arm", "arm64", "native"], case_sensitive=False),
    help="Target architecture (overrides config)",
)
@click.option(
    "--cross-compile",
    help="Cross-compiler prefix override (e.g. arm-linux-gnueabihf-)",
)
@click.option(
    "--tinyiiod-path",
    type=click.Path(),
    help="Path to cross-compiled libtinyiiod (must contain include/ and lib/)",
)
@click.option(
    "--libiio-path",
    type=click.Path(),
    help="Path to cross-compiled libiio (must contain include/ and lib/)",
)
@click.option("--clean", is_flag=True, help="Remove build directory before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel make jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Write a bash build script instead of building",
)
@click.pass_context
def build_iio_emu(
    ctx,
    platform,
    tag,
    arch,
    cross_compile,
    tinyiiod_path,
    libiio_path,
    clean,
    jobs,
    generate_script,
):
    """
    Build the iio-emu server application.

    Clones https://github.com/analogdevicesinc/iio-emu, configures it
    with CMake, and builds the emulator for the target architecture.
    Requires libtinyiiod and libiio; for cross-compiled targets supply
    pre-built paths via --tinyiiod-path and --libiio-path.

    Example:

        adibuild --config configs/iio_emu/default.yaml iio-emu build -p native
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="iio_emu",
        )

        platform_obj = get_platform_instance(config, platform)

        # Apply CLI overrides to platform config
        if arch:
            platform_obj.config["arch"] = arch
        if cross_compile:
            platform_obj.config["cross_compile"] = cross_compile
        if tinyiiod_path:
            platform_obj.config["tinyiiod_path"] = tinyiiod_path
        if libiio_path:
            platform_obj.config["libiio_path"] = libiio_path

        builder = IIOEmuBuilder(config, platform_obj, script_mode=generate_script)
        result = builder.build(clean_before=clean, jobs=jobs)

        if generate_script:
            print_success(
                f"Build script written to {result.get('script', 'build script')}"
            )
        else:
            print_success(
                f"iio-emu built successfully. "
                f"{len(result.get('artifacts', []))} artifact(s) in "
                f"{result.get('output_dir', '')}"
            )

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@iio_emu.command(name="clean")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option(
    "--deep",
    is_flag=True,
    help="Remove entire build directory (default: make clean)",
)
@click.pass_context
def clean_iio_emu(ctx, platform, tag, deep):
    """
    Clean iio-emu build artifacts.

    By default runs ``make clean`` inside the build directory.
    Use --deep to remove the entire build directory tree.
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="iio_emu",
        )

        platform_obj = get_platform_instance(config, platform)
        builder = IIOEmuBuilder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# Genalyzer command group
@cli.group()
def genalyzer():
    """Genalyzer DSP analysis library build commands."""
    pass


@genalyzer.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config (e.g. arm, arm64, native)",
)
@click.option("--tag", "-t", help="Git tag or branch (e.g. main, v0.1.2)")
@click.option(
    "--arch",
    type=click.Choice(["arm", "arm64", "native"], case_sensitive=False),
    help="Target architecture (overrides config)",
)
@click.option(
    "--cross-compile",
    help="Cross-compiler prefix override (e.g. arm-linux-gnueabihf-)",
)
@click.option(
    "--fftw-path",
    type=click.Path(),
    help="Path to pre-built FFTW3 installation (must contain include/ and lib/)",
)
@click.option("--clean", is_flag=True, help="Remove build directory before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel make jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Write a bash build script instead of building",
)
@click.pass_context
def build_genalyzer(
    ctx, platform, tag, arch, cross_compile, fftw_path, clean, jobs, generate_script
):
    """
    Build the genalyzer DSP analysis library.

    Clones https://github.com/analogdevicesinc/genalyzer, configures it
    with CMake, and builds a shared library for the target architecture.
    Requires FFTW3 on the build host; for cross-compiled targets supply
    a pre-built FFTW3 via --fftw-path.

    Example:

        adibuild --config configs/genalyzer/default.yaml genalyzer build -p native
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="genalyzer",
        )

        platform_obj = get_platform_instance(config, platform)

        # Apply CLI overrides to platform config
        if arch:
            platform_obj.config["arch"] = arch
        if cross_compile:
            platform_obj.config["cross_compile"] = cross_compile
        if fftw_path:
            platform_obj.config["fftw_path"] = fftw_path

        builder = GenalyzerBuilder(config, platform_obj, script_mode=generate_script)
        result = builder.build(clean_before=clean, jobs=jobs)

        if generate_script:
            print_success(
                f"Build script written to {result.get('script', 'build script')}"
            )
        else:
            print_success(
                f"genalyzer built successfully. "
                f"{len(result.get('artifacts', []))} artifact(s) in "
                f"{result.get('output_dir', '')}"
            )

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@genalyzer.command(name="clean")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name from config",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option(
    "--deep",
    is_flag=True,
    help="Remove entire build directory (default: make clean)",
)
@click.pass_context
def clean_genalyzer(ctx, platform, tag, deep):
    """
    Clean genalyzer build artifacts.

    By default runs ``make clean`` inside the build directory.
    Use --deep to remove the entire build directory tree.
    """
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="genalyzer",
        )

        platform_obj = get_platform_instance(config, platform)
        builder = GenalyzerBuilder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# Linux kernel command group
@cli.group()
def linux():
    """Linux kernel build commands."""
    pass


@linux.command(name="build")
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch to build")
@click.option("--defconfig", help="Override defconfig")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--dtbs-only", is_flag=True, help="Build only device tree blobs")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Generate bash script instead of executing build",
)
@click.option(
    "--simpleimage",
    "-s",
    "simpleimage_targets",
    multiple=True,
    help="MicroBlaze simpleImage target(s) to build (only valid with -p microblaze)",
)
@click.option(
    "--simpleimage-preset",
    "-sp",
    "simpleimage_preset",
    is_flag=True,
    help="Interactively select simpleImage from predefined presets (requires -t tag, microblaze only)",
)
@click.option(
    "--carrier",
    "-c",
    "carrier",
    help="Filter simpleImage presets by carrier board (e.g., vcu118, kcu105)",
)
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override toolchain version (e.g., 2023.2). Auto-detected from tag if not specified.",
)
@click.option(
    "--allow-any-vivado",
    is_flag=True,
    help="Allow any Vivado version instead of requiring exact match from tag.",
)
@click.pass_context
def build_linux(
    ctx,
    platform,
    tag,
    defconfig,
    output,
    clean,
    dtbs_only,
    jobs,
    generate_script,
    simpleimage_targets,
    simpleimage_preset,
    carrier,
    tool_version,
    allow_any_vivado,
):
    """
    Build Linux kernel for specified platform.

    Examples:

        adibuild linux build -p zynqmp -t 2023_R2

        adibuild linux build -p zynq --clean

        adibuild linux build -p microblaze --simpleimage simpleImage.vcu118_ad9081

        adibuild linux build -p microblaze -t 2023_R2 --simpleimage-preset

        adibuild linux build -p microblaze -t 2023_R2 -sp --carrier vcu118

        adibuild linux build -p zynqmp --generate-script
    """
    # Validate --simpleimage is only for microblaze
    if simpleimage_targets and platform.lower() != "microblaze":
        print_error(
            "The --simpleimage option is only valid for MicroBlaze platform builds."
        )
        return

    # Validate --carrier requires --simpleimage-preset
    if carrier and not simpleimage_preset:
        print_error("--carrier requires --simpleimage-preset to be specified.")
        return

    # Validate --simpleimage-preset requirements
    if simpleimage_preset:
        if platform.lower() != "microblaze":
            print_error("--simpleimage-preset is only valid for MicroBlaze platform.")
            return
        if not tag:
            print_error("--simpleimage-preset requires -t/--tag to be specified.")
            return
        if simpleimage_targets:
            print_error("Cannot use both --simpleimage and --simpleimage-preset.")
            return

        # Load presets and prompt for selection
        from adibuild.cli.helpers import (
            get_simpleimage_presets,
            prompt_simpleimage_selection,
        )

        presets = get_simpleimage_presets(tag, carrier=carrier)
        if not presets:
            if carrier:
                print_error(
                    f"No simpleImage presets found for tag '{tag}' and carrier '{carrier}'."
                )
            else:
                print_error(f"No simpleImage presets found for tag '{tag}'.")
            return

        # Group by carrier only when no specific carrier filter is applied
        selected_target = prompt_simpleimage_selection(
            presets, group_by_carrier=(carrier is None)
        )
        simpleimage_targets = (selected_target,)  # Convert to tuple for consistency

    # Derive tool version from tag if not explicitly specified
    if not tool_version and tag:
        tool_version = tag_to_tool_version(tag)
        if tool_version:
            click.echo(f"Auto-detected tool version {tool_version} from tag {tag}")

    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="linux",
        )

        # Override parallel jobs if specified
        if jobs:
            config.set("build.parallel_jobs", jobs)

        # Override output directory if specified
        if output:
            config.set("build.output_dir", output)

        # Override defconfig if specified
        if defconfig:
            platform_config = config.get_platform(platform)
            platform_config["defconfig"] = defconfig
            config.set(f"platforms.{platform}", platform_config)

        # Override simpleimage_targets if specified
        if simpleimage_targets:
            platform_config = config.get_platform(platform)
            platform_config["simpleimage_targets"] = list(simpleimage_targets)
            platform_config["kernel_target"] = simpleimage_targets[0]
            config.set(f"platforms.{platform}", platform_config)

        # Set tool_version and strict_version in platform config for toolchain selection
        if tool_version:
            platform_config = config.get_platform(platform)
            platform_config["tool_version"] = tool_version
            # Enable strict mode unless --allow-any-vivado is used
            platform_config["strict_version"] = not allow_any_vivado
            config.set(f"platforms.{platform}", platform_config)

        # Remove arm compiler if building for microblaze, to avoid confusion in toolchain selection
        if platform.lower() == "microblaze":
            platform_config = config.get_platform(platform)
            toolchain_config = platform_config.get("toolchain", {})
            # Remove arm and system from fallback options for microblaze
            toolchain_config["fallback"] = []
            platform_config["toolchain"] = toolchain_config
            config.set(f"platforms.{platform}", platform_config)

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj, script_mode=generate_script)

        # Execute build
        result = builder.build(clean_before=clean, dtbs_only=dtbs_only)

        # Display summary
        display_build_summary(result, platform_obj)

    except BuildError as e:
        print_error(f"Build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        if ctx.obj.get("verbose", 0) > 1:
            import traceback

            traceback.print_exc()


@linux.command()
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--defconfig", help="Override defconfig")
@click.pass_context
def configure(ctx, platform, tag, defconfig):
    """
    Configure kernel without building.

    Runs defconfig and prepares the kernel for building.
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="linux",
        )

        # Override defconfig if specified
        if defconfig:
            platform_config = config.get_platform(platform)
            platform_config["defconfig"] = defconfig
            config.set(f"platforms.{platform}", platform_config)

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj)

        # Prepare and configure
        builder.prepare_source()
        builder.configure()

        print_success("Kernel configured successfully")

    except BuildError as e:
        print_error(f"Configuration failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@linux.command()
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.pass_context
def menuconfig(ctx, platform, tag):
    """
    Run interactive kernel configuration (menuconfig).

    Requires ncurses libraries to be installed.
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="linux",
        )

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj)

        # Prepare source and run menuconfig
        builder.prepare_source()
        builder.configure(menuconfig=True)

        print_success("Menuconfig completed")

    except BuildError as e:
        print_error(f"Menuconfig failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@linux.command()
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.argument("dtb_files", nargs=-1)
@click.pass_context
def dtbs(ctx, platform, tag, dtb_files):
    """
    Build specific device tree blobs.

    Examples:

        adibuild linux dtbs -p zynqmp zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

        adibuild linux dtbs -p zynq zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="linux",
        )

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj)

        # Prepare and configure
        builder.prepare_source()
        builder.configure()

        # Build specified DTBs or all from config
        dtb_list = list(dtb_files) if dtb_files else None
        built_dtbs = builder.build_dtbs(dtbs=dtb_list)

        print_success(f"Built {len(built_dtbs)} DTBs successfully")

    except BuildError as e:
        print_error(f"DTB build failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


@linux.command()
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--deep", is_flag=True, help="Use mrproper instead of distclean")
@click.pass_context
def clean(ctx, platform, tag, deep):
    """
    Clean kernel build artifacts.

    By default uses 'make distclean' (removes all generated files + config).
    Use --deep for mrproper (same but without removing editor backup files).
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="linux",
        )

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj)

        # Prepare source
        builder.prepare_source()

        # Clean
        builder.clean(deep=deep)

        print_success("Clean completed")

    except BuildError as e:
        print_error(f"Clean failed: {e}")
    except Exception as e:
        print_error(f"Unexpected error: {e}")


# Toolchain commands
@cli.command()
@click.option(
    "--platform",
    "-p",
    type=click.Choice(["zynq", "zynqmp", "microblaze"], case_sensitive=False),
    help="Show toolchain for specific platform",
)
@click.pass_context
def toolchain(ctx, platform):
    """
    Detect and display available toolchains.

    Shows which toolchains are available and which would be selected.
    """
    try:
        from adibuild.core.toolchain import (
            ArmToolchain,
            SystemToolchain,
            VivadoToolchain,
        )

        click.echo("Detecting available toolchains...\n")

        # Check Vivado
        vivado = VivadoToolchain()
        vivado_info = vivado.detect()
        if vivado_info:
            click.echo("✓ Vivado/Vitis Toolchain:")
            display_toolchain_info(vivado_info)
            click.echo()
        else:
            click.echo(
                "✗ Vivado/Vitis toolchain not found "
                "(install with 'adibuild vivado install --version <version>')\n"
            )

        # Check ARM GNU
        arm = ArmToolchain()
        arm_info = arm.detect()
        if arm_info:
            click.echo("✓ ARM GNU Toolchain:")
            display_toolchain_info(arm_info)
            click.echo()
        else:
            click.echo("✗ ARM GNU toolchain not found (can be auto-downloaded)\n")

        # Check System
        system = SystemToolchain()
        system_info = system.detect()
        if system_info:
            click.echo("✓ System Toolchain:")
            display_toolchain_info(system_info)
            click.echo()
        else:
            click.echo("✗ System cross-compiler not found\n")

        # Show selected toolchain for platform if specified
        if platform:
            config_path = ctx.obj.get("config_path")
            if config_path:
                config = BuildConfig.from_yaml(config_path)
            else:
                # Load default config
                config_dir = Path(__file__).parent.parent.parent / "configs" / "linux"
                default_config = config_dir / f"{platform}.yaml"
                config = BuildConfig.from_yaml(default_config)

            platform_obj = get_platform_instance(config, platform)
            selected = platform_obj.get_toolchain()

            click.echo(f"\n[Selected for {platform}]")
            display_toolchain_info(selected)

    except Exception as e:
        print_error(f"Toolchain detection failed: {e}")


@cli.group()
def vivado():
    """Vivado download, installation, and detection commands."""
    pass


@vivado.command("list")
@click.option(
    "--install-dir",
    type=click.Path(),
    help="Optional Vivado installation root (defaults to standard search paths)",
)
def vivado_list(install_dir):
    """List supported Vivado releases and local installation status."""
    from adibuild.core.vivado import VivadoInstaller

    installer = VivadoInstaller()
    root = Path(install_dir) if install_dir else None

    click.echo("Supported Vivado releases:\n")
    for release in installer.list_supported_releases():
        info = installer.status(release.version, root)
        status = "installed" if info else "not installed"
        path = str(info.path) if info else "-"
        click.echo(f"{release.version:<8} {status:<13} {path}")


@vivado.command("detect")
@click.option("--version", help="Vivado version to detect (e.g. 2023.2)")
@click.option(
    "--install-dir",
    type=click.Path(),
    help="Optional Vivado installation root (e.g. /opt/Xilinx)",
)
def vivado_detect(version, install_dir):
    """Detect an installed Vivado release."""
    from adibuild.core.vivado import VivadoInstaller

    installer = VivadoInstaller()
    info = installer.status(
        version=version, install_dir=Path(install_dir) if install_dir else None
    )
    if info:
        display_toolchain_info(info)
        return

    target = version or "supported versions"
    print_error(f"No installed Vivado toolchain detected for {target}")


@vivado.command("status")
@click.option("--version", help="Vivado version to detect (e.g. 2023.2)")
@click.option(
    "--install-dir",
    type=click.Path(),
    help="Optional Vivado installation root (e.g. /opt/Xilinx)",
)
def vivado_status(version, install_dir):
    """Alias for 'vivado detect'."""
    ctx = click.get_current_context()
    ctx.invoke(vivado_detect, version=version, install_dir=install_dir)


@vivado.group("image")
def vivado_image():
    """Reusable Docker image management for Vivado-based builds."""
    pass


@vivado_image.command("build")
@click.option("--version", required=True, help="Vivado version to install into the image")
@click.option("--tag", help="Docker image tag (defaults to adibuild/vivado:<version>)")
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Override the Vivado cache directory used for staging",
)
@click.option(
    "--installer-path",
    type=click.Path(exists=True),
    help="Use a pre-downloaded self-extracting installer instead of downloading one",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True),
    help="Optional xsetup batch config file",
)
@click.option(
    "--base-image",
    default="ubuntu:22.04",
    show_default=True,
    help="Base image used to build the reusable Vivado image",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Do not prompt for AMD credentials; rely on environment variables",
)
def vivado_image_build(
    version,
    tag,
    cache_dir,
    installer_path,
    config_path,
    base_image,
    non_interactive,
):
    """Build a reusable Docker image with Vivado preinstalled."""
    from adibuild.core.docker import VivadoDockerImageManager

    credentials = _load_vivado_credentials(non_interactive=non_interactive)
    manager = VivadoDockerImageManager(cache_dir=Path(cache_dir) if cache_dir else None)
    try:
        result = manager.build_image(
            version,
            tag=tag,
            credentials=credentials,
            installer_path=Path(installer_path) if installer_path else None,
            config_path=Path(config_path) if config_path else None,
            base_image=base_image,
        )
    except Exception as exc:
        print_error(f"Vivado image build failed: {exc}")

    print_success(
        f"Built reusable Vivado image {result['tag']} for Vivado {result['version']}"
    )


@vivado_image.command("list")
def vivado_image_list():
    """List reusable Vivado Docker images."""
    from adibuild.core.docker import VivadoDockerImageManager

    manager = VivadoDockerImageManager()
    try:
        images = manager.list_images()
    except Exception as exc:
        print_error(f"Failed to list Vivado images: {exc}")

    if not images:
        click.echo("No reusable Vivado images found.")
        return

    for image in images:
        click.echo(
            f"{image.get('Repository')}:{image.get('Tag')}  "
            f"{image.get('ID')}  {image.get('CreatedSince')}"
        )


@vivado_image.command("inspect")
@click.option("--tag", required=True, help="Docker image tag to inspect")
def vivado_image_inspect(tag):
    """Inspect a reusable Vivado Docker image."""
    from adibuild.core.docker import VivadoDockerImageManager

    manager = VivadoDockerImageManager()
    try:
        image = manager.inspect_image(tag)
    except Exception as exc:
        print_error(f"Failed to inspect Vivado image: {exc}")

    click.echo(json.dumps(image, indent=2, sort_keys=True))


@vivado.command("install")
@click.option("--version", required=True, help="Vivado version to install")
@click.option(
    "--install-dir",
    type=click.Path(),
    default="/opt/Xilinx",
    show_default=True,
    help="Vivado installation root",
)
@click.option(
    "--cache-dir",
    type=click.Path(),
    help="Override the cache directory used for installers and extracted clients",
)
@click.option(
    "--extract-dir",
    type=click.Path(),
    help="Override the extracted web installer client directory",
)
@click.option(
    "--installer-path",
    type=click.Path(exists=True),
    help="Use a pre-downloaded self-extracting installer instead of downloading one",
)
@click.option(
    "--config-path",
    type=click.Path(exists=True),
    help="Optional xsetup batch config file",
)
@click.option(
    "--edition",
    help="Vivado edition to install when no config file is provided",
)
@click.option(
    "--download-only",
    is_flag=True,
    help="Download and cache the official installer binary, then stop",
)
@click.option(
    "--non-interactive",
    is_flag=True,
    help="Do not prompt for AMD credentials; rely on environment variables",
)
@click.option(
    "--no-webtalk",
    is_flag=True,
    help="Do not accept WebTalk terms automatically",
)
def vivado_install(
    version,
    install_dir,
    cache_dir,
    extract_dir,
    installer_path,
    config_path,
    edition,
    download_only,
    non_interactive,
    no_webtalk,
):
    """Download and install Vivado on Linux."""
    from adibuild.core.vivado import VivadoInstaller, VivadoInstallRequest

    cache_path = Path(cache_dir) if cache_dir else None
    installer = VivadoInstaller(cache_dir=cache_path)
    credentials = _load_vivado_credentials(non_interactive=non_interactive)
    click.echo(
        f"Vivado install request: version={version}, install_dir={install_dir}, "
        f"mode={'download-only' if download_only else 'install'}"
    )
    if cache_path:
        click.echo(f"Using Vivado cache directory: {cache_path}")
    if installer_path:
        click.echo(f"Using pre-downloaded installer: {installer_path}")
    if config_path:
        click.echo(f"Using xsetup config file: {config_path}")
    click.echo(
        "Credential source: "
        + ("environment/prompt provided" if credentials else "config-file-only flow")
    )

    try:
        if download_only:
            click.echo("Starting Vivado installer download...")
            path = installer.download_installer(
                version=version,
                cache_dir=cache_path / "installers" if cache_path else None,
                credentials=credentials,
            )
            print_success(f"Downloaded Vivado {version} installer to {path}")
            return

        click.echo("Starting Vivado installation workflow...")
        result = installer.install(
            VivadoInstallRequest(
                version=version,
                install_dir=Path(install_dir),
                cache_dir=cache_path,
                extract_dir=Path(extract_dir) if extract_dir else None,
                installer_path=Path(installer_path) if installer_path else None,
                config_path=Path(config_path) if config_path else None,
                edition=edition,
                agree_webtalk_terms=not no_webtalk,
                credentials=credentials,
            )
        )
        print_success(
            f"Installed Vivado {result.release.version} to {result.toolchain.path}"
        )
    except Exception as e:
        print_error(f"Vivado installation failed: {e}")


# Configuration commands
@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command("init")
def config_init():
    """
    Initialize global configuration file.

    Creates ~/.adibuild/config.yaml with default settings.
    """
    config_path = Path.home() / ".adibuild" / "config.yaml"

    if config_path.exists():
        if not click.confirm(
            f"Configuration already exists at {config_path}. Overwrite?"
        ):
            return

    create_default_config(config_path)


@config.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def config_validate(config_file):
    """
    Validate configuration file against schema.

    Checks if configuration file is valid according to the JSON schema.
    """
    schema_path = (
        Path(__file__).parent.parent.parent
        / "configs"
        / "schema"
        / "linux_config.schema.json"
    )

    if not schema_path.exists():
        print_error(f"Schema file not found: {schema_path}")

    validate_config_file(Path(config_file), schema_path)


@config.command("show")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file to show",
)
def config_show(config):
    """
    Display configuration and available platforms.
    """
    try:
        if config:
            config_obj = BuildConfig.from_yaml(config)
        else:
            # Try default configs
            config_dir = Path(__file__).parent.parent.parent / "configs" / "linux"
            default_config = config_dir / "2023_R2.yaml"
            config_obj = BuildConfig.from_yaml(default_config)

        display_platforms(config_obj)

    except Exception as e:
        print_error(f"Failed to load configuration: {e}")


@cli.command()
def mcp():
    """
    Start the MCP server.
    """
    try:
        from adibuild.cli.mcp_server import mcp

        mcp.run()
    except ImportError:
        print_error(
            "fastmcp is not installed. Please install with 'pip install fastmcp'."
        )
    except Exception as e:
        print_error(f"Failed to start MCP server: {e}")


@cli.group()
def boot():
    """Bootloader and BOOT.BIN build commands."""
    pass


@boot.command(name="build-atf")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name (e.g. zynqmp)",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override Vivado version used to select the reusable Docker image.",
)
@click.option(
    "--runner",
    type=click.Choice(["local", "docker"]),
    help="Execution backend for the build",
)
@click.option("--docker-image", help="Reusable Docker image tag for --runner docker")
@click.pass_context
def build_atf(ctx, platform, tag, clean, jobs, tool_version, runner, docker_image):
    """Build ARM Trusted Firmware (ATF)."""
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="atf",
        )
        platform_config = config.get_platform(platform)
        resolved_runner, resolved_image, resolved_tool_version = _resolve_docker_runner(
            config,
            platform_config,
            runner,
            docker_image,
            tool_version,
            tag,
        )
        platform_obj = get_platform_instance(config, platform)
        builder = ATFBuilder(
            config,
            platform_obj,
            runner=resolved_runner,
            docker_image=resolved_image,
            docker_tool_version=resolved_tool_version,
        )
        result = builder.build(clean_before=clean, jobs=jobs)
        print_success(f"ATF build completed. bl31.elf in: {result['output_dir']}")
    except BuildError as e:
        print_error(f"ATF build failed: {e}")


@boot.command(name="build-uboot")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name (e.g. zynqmp, zynq)",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--defconfig", help="Override U-Boot defconfig")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override Vivado version used to select the reusable Docker image.",
)
@click.option(
    "--runner",
    type=click.Choice(["local", "docker"]),
    help="Execution backend for the build",
)
@click.option("--docker-image", help="Reusable Docker image tag for --runner docker")
@click.pass_context
def build_uboot(
    ctx,
    platform,
    tag,
    defconfig,
    clean,
    jobs,
    tool_version,
    runner,
    docker_image,
):
    """Build U-Boot bootloader."""
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="uboot",
        )
        if defconfig:
            config.set("uboot.defconfig", defconfig)
        platform_config = config.get_platform(platform)
        resolved_runner, resolved_image, resolved_tool_version = _resolve_docker_runner(
            config,
            platform_config,
            runner,
            docker_image,
            tool_version,
            tag,
        )
        platform_obj = get_platform_instance(config, platform)
        builder = UBootBuilder(
            config,
            platform_obj,
            runner=resolved_runner,
            docker_image=resolved_image,
            docker_tool_version=resolved_tool_version,
        )
        result = builder.build(clean_before=clean, jobs=jobs)
        print_success(f"U-Boot build completed. Artifacts in: {result['output_dir']}")
    except BuildError as e:
        print_error(f"U-Boot build failed: {e}")


@boot.command(name="build-boot")
@click.option(
    "--platform",
    "-p",
    required=True,
    help="Platform name (e.g. zynqmp, zynq, versal)",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--xsa", type=click.Path(exists=True), help="Path to XSA file")
@click.option("--bit", type=click.Path(exists=True), help="Path to bitstream file")
@click.option(
    "--dtb", type=click.Path(exists=True), help="Path to device tree blob (.dtb)"
)
@click.option("--pdi", type=click.Path(exists=True), help="Path to PDI file (Versal)")
@click.option("--atf", type=click.Path(exists=True), help="Path to pre-built bl31.elf")
@click.option(
    "--uboot", type=click.Path(exists=True), help="Path to pre-built u-boot.elf"
)
@click.option("--fsbl", type=click.Path(exists=True), help="Path to pre-built FSBL")
@click.option("--pmufw", type=click.Path(exists=True), help="Path to pre-built PMUFW")
@click.option(
    "--plm", type=click.Path(exists=True), help="Path to pre-built PLM (Versal)"
)
@click.option(
    "--psmfw", type=click.Path(exists=True), help="Path to pre-built PSMFW (Versal)"
)
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.option(
    "--generate-script",
    is_flag=True,
    help="Generate bash script instead of executing build",
)
@click.option(
    "--tool-version",
    "-tv",
    "tool_version",
    help="Override Vivado version used to select the reusable Docker image.",
)
@click.option(
    "--runner",
    type=click.Choice(["local", "docker"]),
    help="Execution backend for the build",
)
@click.option("--docker-image", help="Reusable Docker image tag for --runner docker")
@click.pass_context
def build_boot(
    ctx,
    platform,
    tag,
    xsa,
    bit,
    dtb,
    pdi,
    atf,
    uboot,
    fsbl,
    pmufw,
    plm,
    psmfw,
    clean,
    jobs,
    generate_script,
    tool_version,
    runner,
    docker_image,
):
    """Generate BOOT.BIN for Zynq, ZynqMP or Versal."""
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="boot",
        )
        if xsa:
            config.set("boot.xsa_path", xsa)
        if bit:
            config.set("boot.bit_path", bit)
        if dtb:
            config.set("boot.dtb_path", dtb)
        if pdi:
            config.set("boot.pdi_path", pdi)
        if atf:
            config.set("boot.atf_path", atf)
        if uboot:
            config.set("boot.uboot_path", uboot)
        if fsbl:
            config.set("boot.fsbl_path", fsbl)
        if pmufw:
            config.set("boot.pmufw_path", pmufw)
        if plm:
            config.set("boot.plm_path", plm)
        if psmfw:
            config.set("boot.psmfw_path", psmfw)

        platform_config = config.get_platform(platform)
        resolved_runner, resolved_image, resolved_tool_version = _resolve_docker_runner(
            config,
            platform_config,
            runner,
            docker_image,
            tool_version,
            tag,
        )
        platform_obj = get_platform_instance(config, platform)
        builder = BootBuilder(
            config,
            platform_obj,
            script_mode=generate_script,
            runner=resolved_runner,
            docker_image=resolved_image,
            docker_tool_version=resolved_tool_version,
        )
        result = builder.build(clean_before=clean, jobs=jobs)
        print_success(f"BOOT.BIN generated: {result['boot_bin']}")
    except BuildError as e:
        print_error(f"BOOT.BIN generation failed: {e}")


@boot.command(name="build-zynqmp-boot", hidden=True)
@click.pass_context
def build_zynqmp_boot_alias(ctx, **kwargs):
    """Alias for build-boot."""
    ctx.invoke(build_boot, **kwargs)


# Main entry point
def main():
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
