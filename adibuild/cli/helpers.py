"""CLI helper functions and utilities."""

import sys
from pathlib import Path
from typing import Dict, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from adibuild import __version__
from adibuild.core.config import BuildConfig, ConfigurationError
from adibuild.core.toolchain import ToolchainInfo
from adibuild.platforms.base import Platform
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.platforms.microblaze import MicroBlazePlatform


console = Console()


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
    config_file: Optional[str],
    platform: str,
    tag: Optional[str],
) -> BuildConfig:
    """
    Load configuration with command-line overrides.

    Args:
        config_file: Optional configuration file path
        platform: Platform name
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

            # Try platform-specific config first
            platform_config = config_dir / f"{platform}.yaml"
            if platform_config.exists():
                config = BuildConfig.from_yaml(platform_config)
            else:
                # Try 2023_R2 config
                default_config = config_dir / "2023_R2.yaml"
                if default_config.exists():
                    config = BuildConfig.from_yaml(default_config)
                else:
                    raise ConfigurationError(
                        f"No configuration file found. Please specify with --config"
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


def display_build_summary(result: Dict, platform: Platform):
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


def prompt_for_config() -> Dict:
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
