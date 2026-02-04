from pathlib import Path

from fastmcp import FastMCP

from adibuild import __version__
from adibuild.core.config import BuildConfig, ConfigurationError
from adibuild.platforms.hdl import HDLPlatform
from adibuild.platforms.microblaze import MicroBlazePlatform
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform
from adibuild.projects.hdl import HDLBuilder
from adibuild.projects.linux import LinuxBuilder

# Initialize FastMCP server
mcp = FastMCP("pyadi-build")


def _get_platform_instance(config: BuildConfig, platform_name: str):
    """
    Get platform instance from configuration (Safe version).
    """
    platform_config = config.get_platform(platform_name)
    # Inject platform name into config
    platform_config["name"] = platform_name

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
        raise ValueError(f"Unsupported platform: {platform_name}")


def _load_config(config_file: str | None, platform: str | None = None) -> BuildConfig:
    """
    Load configuration (Safe version).
    """
    if config_file:
        return BuildConfig.from_yaml(config_file)

    # Try to load default configs
    # We assume we are in adibuild/cli/mcp_server.py, so go up 3 levels
    config_dir = Path(__file__).parent.parent.parent / "configs" / "linux"

    # Try platform-specific config first if platform provided
    platform_config = config_dir / f"{platform}.yaml" if platform else None
    if platform_config and platform_config.exists():
        return BuildConfig.from_yaml(platform_config)

    # Try 2023_R2 config
    default_config = config_dir / "2023_R2.yaml"
    if default_config.exists():
        return BuildConfig.from_yaml(default_config)

    raise ConfigurationError("No configuration file found and no default available.")


@mcp.tool()
def get_version() -> str:
    """Return the current version of pyadi-build."""
    return __version__


@mcp.tool()
def list_platforms(config_path: str = None) -> list[str]:
    """List available platforms from the configuration."""
    try:
        config = _load_config(config_path)
        return list(config.config.get("platforms", {}).keys())
    except Exception as e:
        return [f"Error: {str(e)}"]


@mcp.tool()
def build_hdl_project(
    project: str,
    carrier: str,
    arch: str = "unknown",
    clean: bool = False,
    tool_version: str = None,
) -> str:
    """Build an HDL project for a specific project/carrier combination.

    Args:
        project: HDL project name (e.g. fmcomms2)
        carrier: Carrier board name (e.g. zed)
        arch: Architecture (e.g. arm, arm64)
        clean: Whether to clean before building
        tool_version: Override Vivado version (e.g., 2023.2)
    """
    try:
        platform_name = f"{carrier}_{project}"

        # Construct a minimal config for HDL
        platform_config = {
            "hdl_project": project,
            "carrier": carrier,
            "arch": arch,
            "name": platform_name,
        }
        if tool_version:
            platform_config["tool_version"] = tool_version

        config_data = {
            "platforms": {platform_name: platform_config},
            "build": {"output_dir": "build"},
        }
        config = BuildConfig(config_data)

        platform_obj = _get_platform_instance(config, platform_name)
        builder = HDLBuilder(config, platform_obj)
        result = builder.build(clean_before=clean)
        return f"HDL Build completed. Artifacts in: {result['output_dir']}"
    except Exception as e:
        return f"Build failed: {str(e)}"


@mcp.tool()
def list_simpleimage_presets(tag: str, carrier: str = None) -> list[dict]:
    """List available simpleImage presets for a given release tag.

    Args:
        tag: Release tag (e.g., 2023_R2, 2022_R2)
        carrier: Optional carrier filter (e.g., vcu118, kcu105)

    Returns:
        List of preset configurations with project, carrier, and simpleimage_target
    """
    try:
        from adibuild.cli.helpers import get_simpleimage_presets

        return get_simpleimage_presets(tag, carrier)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def build_linux_platform(
    platform: str,
    config_path: str = None,
    clean: bool = False,
    simpleimage_targets: list[str] = None,
    tool_version: str = None,
    allow_any_vivado: bool = False,
) -> str:
    """Build Linux kernel for a specific platform.

    Args:
        platform: Target platform (e.g., zynq, zynqmp, microblaze)
        config_path: Path to configuration file
        clean: Whether to clean before building
        simpleimage_targets: List of simpleImage targets for MicroBlaze builds
        tool_version: Override toolchain version (e.g., 2023.2)
        allow_any_vivado: Allow any Vivado version instead of requiring exact match
    """
    try:
        if simpleimage_targets and platform.lower() != "microblaze":
            return (
                "Error: simpleimage_targets is only valid for MicroBlaze platform builds"
            )

        config = _load_config(config_path, platform)

        if simpleimage_targets:
            platform_config = config.get_platform(platform)
            platform_config["simpleimage_targets"] = simpleimage_targets
            platform_config["kernel_target"] = simpleimage_targets[0]
            config.set(f"platforms.{platform}", platform_config)

        if tool_version:
            platform_config = config.get_platform(platform)
            platform_config["tool_version"] = tool_version
            # Enable strict mode unless allow_any_vivado is set
            platform_config["strict_version"] = not allow_any_vivado
            config.set(f"platforms.{platform}", platform_config)

        platform_obj = _get_platform_instance(config, platform)
        builder = LinuxBuilder(config, platform_obj)
        result = builder.build(clean_before=clean)
        return f"Linux Build completed. Output: {result.get('output_dir', 'unknown')}"
    except Exception as e:
        return f"Build failed: {str(e)}"
