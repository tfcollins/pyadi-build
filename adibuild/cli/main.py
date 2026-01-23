"""Command-line interface for adibuild."""

import logging
import sys
from pathlib import Path
from typing import Optional

import click

from adibuild import __version__
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
    validate_config_file,
)
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.projects.linux import LinuxBuilder
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


# Linux kernel command group
@cli.group()
def linux():
    """Linux kernel build commands."""
    pass


@linux.command()
@click.option(
    "--platform",
    "-p",
    required=True,
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch to build")
@click.option("--defconfig", help="Override defconfig")
@click.option("--output", "-o", type=click.Path(), help="Output directory")
@click.option("--clean", is_flag=True, help="Clean before building")
@click.option("--dtbs-only", is_flag=True, help="Build only device tree blobs")
@click.option("--jobs", "-j", type=int, help="Number of parallel jobs")
@click.pass_context
def build(ctx, platform, tag, defconfig, output, clean, dtbs_only, jobs):
    """
    Build Linux kernel for specified platform.

    Examples:

        adibuild linux build -p zynqmp -t 2023_R2

        adibuild linux build -p zynq --clean

        adibuild linux build -p zynqmp --dtbs-only
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
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

        # Get platform instance
        platform_obj = get_platform_instance(config, platform)

        # Create builder
        builder = LinuxBuilder(config, platform_obj)

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
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
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
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
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
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
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
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
    help="Target platform",
)
@click.option("--tag", "-t", help="Git tag or branch")
@click.option("--deep", is_flag=True, help="Deep clean (mrproper)")
@click.pass_context
def clean(ctx, platform, tag, deep):
    """
    Clean kernel build artifacts.

    Use --deep for full clean (make mrproper).
    """
    try:
        # Load configuration
        config = load_config_with_overrides(
            ctx.obj.get("config_path"),
            platform,
            tag,
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
    type=click.Choice(["zynq", "zynqmp"], case_sensitive=False),
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
            VivadoToolchain,
            ArmToolchain,
            SystemToolchain,
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
        if not click.confirm(f"Configuration already exists at {config_path}. Overwrite?"):
            return

    create_default_config(config_path)


@config.command("validate")
@click.argument("config_file", type=click.Path(exists=True))
def config_validate(config_file):
    """
    Validate configuration file against schema.

    Checks if configuration file is valid according to the JSON schema.
    """
    schema_path = Path(__file__).parent.parent.parent / "configs" / "schema" / "linux_config.schema.json"

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


# Main entry point
def main():
    """Main entry point for CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
