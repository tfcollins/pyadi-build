"""Command-line interface for adibuild."""

import logging
from pathlib import Path

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
from adibuild.projects.libad9361 import LibAD9361Builder
from adibuild.projects.linux import LinuxBuilder
from adibuild.projects.noos import NoOSBuilder
from adibuild.projects.uboot import UBootBuilder
from adibuild.utils.logger import setup_logging


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

        # Get platform instance
        # Note: HDL platforms might just use generic Platform class
        # or we might need specific ones if toolchain logic differs.
        # For now, generic Platform with config dict is enough.
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = HDLBuilder(config, platform_obj, script_mode=generate_script)

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

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = NoOSBuilder(config, platform_obj, script_mode=generate_script)

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
            click.echo("✗ Vivado/Vitis toolchain not found\n")

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
@click.pass_context
def build_atf(ctx, platform, tag, clean, jobs):
    """Build ARM Trusted Firmware (ATF)."""
    try:
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
            project_type="atf",
        )
        platform_obj = get_platform_instance(config, platform)
        builder = ATFBuilder(config, platform_obj)
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
@click.pass_context
def build_uboot(ctx, platform, tag, defconfig, clean, jobs):
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
        platform_obj = get_platform_instance(config, platform)
        builder = UBootBuilder(config, platform_obj)
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

        platform_obj = get_platform_instance(config, platform)
        builder = BootBuilder(config, platform_obj, script_mode=generate_script)
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
