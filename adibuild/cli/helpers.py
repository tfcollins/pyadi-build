"""CLI helper functions and utilities."""

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from adibuild import __version__
from adibuild.core.config import BuildConfig, ConfigurationError
from adibuild.core.toolchain import ToolchainInfo
from adibuild.platforms.base import Platform
from adibuild.platforms.hdl import HDLPlatform
from adibuild.platforms.microblaze import MicroBlazePlatform
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform

console = Console()


def tag_to_tool_version(tag: str) -> str | None:
    """
    Map ADI release tag to tool version.

    Args:
        tag: Release tag (e.g., 2023_R2, 2022_R2_P1, main)

    Returns:
        Tool version string (e.g., "2023.2") or None if tag doesn't match pattern

    Examples:
        2023_R2 -> 2023.2
        2023_R2_P1 -> 2023.2
        2022_R1 -> 2022.1
        main -> None
    """
    if not tag:
        return None

    # Match pattern: YYYY_RN or YYYY_RN_Px (patch releases)
    match = re.match(r"^(\d{4})_R(\d+)(?:_P\d+)?$", tag)
    if match:
        year = match.group(1)
        release = match.group(2)
        return f"{year}.{release}"

    return None


def print_version():
    """Print version information."""
    console.print(f"[bold]adibuild[/bold] version {__version__}")


def print_error(message: str):
    """Print error message and exit."""
    console.print(f"[bold red]Error:[/bold red] {message}")
    sys.exit(1)


def print_success(message: str):
    """Print success message."""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str):
    """Print warning message."""
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")


def load_config_with_overrides(
    config_file: str | None,
    platform: str | None,
    tag: str | None,
) -> BuildConfig:
    """
    Load configuration with command-line overrides.

    Args:
        config_file: Optional configuration file path
        platform: Platform name (optional)
        tag: Optional tag override

    Returns:
        BuildConfig instance
    """
    try:
        if config_file:
            config = BuildConfig.from_yaml(config_file)
        else:
            # Try to load default configs
            config_dir = Path(__file__).parent.parent.parent / "configs" / "linux"

            # Try platform-specific config first if platform provided
            platform_config = config_dir / f"{platform}.yaml" if platform else None
            if platform_config and platform_config.exists():
                config = BuildConfig.from_yaml(platform_config)
            else:
                # Try 2023_R2 config
                default_config = config_dir / "2023_R2.yaml"
                if default_config.exists():
                    config = BuildConfig.from_yaml(default_config)
                else:
                    # If platform was not provided, and default not found,
                    # create empty config if we are in dynamic mode (platform=None)
                    # But if we rely on default configs being present, raise error.
                    # For Linux builds config is usually required.
                    # For HDL builds with --project/--carrier, an empty config might suffice
                    # if we inject platforms later.

                    # Let's return empty config if no file found, to support dynamic builds without config file
                    # provided we assume defaults for missing fields.
                    # Or simpler: require a config file always, but fallback to empty dict
                    # if we are just testing or in a very custom mode.

                    # However, existing logic raised Error. Let's keep existing behavior for now
                    # unless platform is None?

                    # If no default config found, and no user config, raise error
                    raise ConfigurationError(
                        "No configuration file found. Please specify with --config"
                    )

        # Apply tag override
        if tag:
            config.set("tag", tag)

        return config

    except Exception as e:
        print_error(f"Failed to load configuration: {e}")


def get_platform_instance(config: BuildConfig, platform_name: str) -> Platform:
    """
    Get platform instance from configuration.

    Args:
        config: Build configuration
        platform_name: Platform name

    Returns:
        Platform instance
    """

    try:
        platform_config = config.get_platform(platform_name)
        # Inject platform name into config
        platform_config["name"] = platform_name

        # Check if it's a no-OS config
        if platform_config.get("noos_platform") or config.get_project() == "noos":
            from adibuild.platforms.noos import NoOSPlatform

            return NoOSPlatform(platform_config)

        # Check if it's an HDL config
        if platform_config.get("hdl_project") or config.get_project() == "hdl":
            return HDLPlatform(platform_config)

        # Create appropriate platform instance
        arch = platform_config.get("arch")
        if arch == "arm" or platform_name == "zynq":
            return ZynqPlatform(platform_config)
        elif arch == "arm64" or platform_name == "zynqmp":
            return ZynqMPPlatform(platform_config)
        elif arch == "microblaze" or platform_name.startswith("microblaze"):
            return MicroBlazePlatform(platform_config)
        else:
            print_error(f"Unsupported platform: {platform_name}")

    except Exception as e:
        print_error(f"Failed to create platform: {e}")


def display_build_summary(result: dict, platform: Platform):
    """
    Display build summary.

    Args:
        result: Build result dictionary
        platform: Platform instance
    """
    # Create summary table
    table = Table(title="Build Summary", show_header=False, box=None)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Platform", platform.arch)
    table.add_row("Defconfig", platform.defconfig)
    table.add_row("Kernel Target", platform.kernel_target)

    if result.get("kernel_image"):
        table.add_row("Kernel Image", str(result["kernel_image"]))

    dtbs = result.get("dtbs", [])
    if dtbs:
        table.add_row("DTBs Built", str(len(dtbs)))

    if result.get("duration"):
        duration = result["duration"]
        table.add_row("Build Time", f"{duration:.1f}s")

    if result.get("artifacts"):
        table.add_row("Output Directory", str(result["artifacts"]))

    console.print(table)
    print_success("Build completed successfully!")


def display_toolchain_info(toolchain: ToolchainInfo):
    """
    Display toolchain information.

    Args:
        toolchain: ToolchainInfo instance
    """
    table = Table(title="Toolchain Information", show_header=False, box=None)
    table.add_column("Property", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Type", toolchain.type)
    table.add_row("Version", toolchain.version)
    table.add_row("Path", str(toolchain.path))

    if toolchain.cross_compile_arm32:
        table.add_row("ARM32 Prefix", toolchain.cross_compile_arm32)
    if toolchain.cross_compile_arm64:
        table.add_row("ARM64 Prefix", toolchain.cross_compile_arm64)
    if toolchain.cross_compile_microblaze:
        table.add_row("MicroBlaze Prefix", toolchain.cross_compile_microblaze)

    console.print(table)


def display_platforms(config: BuildConfig):
    """
    Display available platforms from configuration.

    Args:
        config: Build configuration
    """
    platforms = config.get("platforms", {})

    if not platforms:
        print_warning("No platforms defined in configuration")
        return

    table = Table(title="Available Platforms")
    table.add_column("Platform", style="cyan", no_wrap=True)
    table.add_column("Architecture", style="white")
    table.add_column("Defconfig", style="yellow")
    table.add_column("Kernel Target", style="green")
    table.add_column("DTBs", style="blue")

    for name, platform_config in platforms.items():
        arch = platform_config.get("arch", "?")
        defconfig = platform_config.get("defconfig", "?")
        target = platform_config.get("kernel_target", "?")
        dtbs = len(platform_config.get("dtbs", []))

        table.add_row(name, arch, defconfig, target, str(dtbs))

    console.print(table)


def validate_config_file(config_path: Path, schema_path: Path):
    """
    Validate configuration file against schema.

    Args:
        config_path: Path to configuration file
        schema_path: Path to JSON schema file
    """
    try:
        config = BuildConfig.from_yaml(config_path)
        config.validate(schema_path)
        print_success(f"Configuration valid: {config_path}")
    except Exception as e:
        print_error(f"Configuration validation failed: {e}")


def prompt_for_config() -> dict:
    """
    Interactively prompt user for configuration.

    Returns:
        Configuration dictionary
    """
    console.print("[bold]Initialize adibuild configuration[/bold]\n")

    config = {
        "build": {},
        "toolchains": {},
    }

    # Parallel jobs
    default_jobs = click.prompt(
        "Default parallel jobs",
        type=int,
        default=8,
    )
    config["build"]["parallel_jobs"] = default_jobs

    # Vivado path
    vivado_path = click.prompt(
        "Xilinx Vivado/Vitis path (optional, press Enter to skip)",
        type=str,
        default="",
        show_default=False,
    )
    if vivado_path:
        config["toolchains"]["vivado_path"] = vivado_path

    return config


def create_default_config(output_path: Path):
    """
    Create default global configuration file.

    Args:
        output_path: Path to write configuration
    """
    config_data = prompt_for_config()

    # Create config object and save
    config = BuildConfig.from_dict(config_data)
    config.to_yaml(output_path)

    print_success(f"Configuration created: {output_path}")


def load_fabric_release_info() -> dict:
    """Load the fabric_release_info.json file."""
    json_path = Path(__file__).parent.parent / "fabric_release_info.json"
    if not json_path.exists():
        raise FileNotFoundError(f"fabric_release_info.json not found at {json_path}")
    with open(json_path) as f:
        return json.load(f)


def get_simpleimage_presets(tag: str, carrier: str = None) -> list[dict]:
    """
    Get available simpleImage presets for a given tag.

    Args:
        tag: Release tag (e.g., 2023_R2, 2022_R2)
        carrier: Optional carrier filter (e.g., vcu118, kcu105)

    Returns:
        List of dicts with keys: project, carrier, simpleimage_target, dts_path
    """
    data = load_fabric_release_info()
    if tag not in data:
        return []

    presets = []
    for project_name, configs in data[tag].items():
        for config in configs:
            if carrier and config["carrier"] != carrier:
                continue
            # Convert dts_path to simpleImage target
            # e.g., "arch/microblaze/boot/dts/vcu118_ad9081.dts" -> "simpleImage.vcu118_ad9081"
            dts_file = Path(config["dts_path"]).stem
            simpleimage_target = f"simpleImage.{dts_file}"
            presets.append(
                {
                    "project": project_name,
                    "carrier": config["carrier"],
                    "simpleimage_target": simpleimage_target,
                    "dts_path": config["dts_path"],
                }
            )
    return presets


def prompt_simpleimage_selection(
    presets: list[dict], group_by_carrier: bool = True
) -> str:
    """
    Prompt user to select a simpleImage preset interactively.

    Args:
        presets: List of preset dicts with project, carrier, simpleimage_target
        group_by_carrier: If True, display presets grouped by carrier

    Returns:
        The selected simpleimage_target
    """
    click.echo("\nAvailable simpleImage presets:")

    options = []  # (number, simpleimage_target)
    idx = 1

    if group_by_carrier:
        # Group presets by carrier
        by_carrier = defaultdict(list)
        for p in presets:
            by_carrier[p["carrier"]].append(p)

        for carrier_name in sorted(by_carrier.keys()):
            click.echo(f"\n  [{carrier_name}]")
            for p in by_carrier[carrier_name]:
                click.echo(f"    {idx}. {p['project']}: {p['simpleimage_target']}")
                options.append((str(idx), p["simpleimage_target"]))
                idx += 1
    else:
        for p in presets:
            click.echo(
                f"  {idx}. {p['carrier']}/{p['project']}: {p['simpleimage_target']}"
            )
            options.append((str(idx), p["simpleimage_target"]))
            idx += 1

    # Prompt for selection
    valid_choices = [opt[0] for opt in options]
    selection = click.prompt(
        "\nSelect preset number",
        type=click.Choice(valid_choices),
        show_choices=False,
    )

    # Return the simpleimage_target for selected option
    return options[int(selection) - 1][1]
