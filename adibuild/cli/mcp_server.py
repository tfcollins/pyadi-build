from pathlib import Path

from fastmcp import FastMCP

from adibuild import __version__
from adibuild.cli.helpers import get_simpleimage_presets, tag_to_tool_version
from adibuild.core.config import BuildConfig, ConfigurationError
from adibuild.core.toolchain import (
    ArmToolchain,
    SystemToolchain,
    VivadoToolchain,
)
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


def _load_config(
    config_file: str | None,
    platform: str | None = None,
    tag: str | None = None,
) -> BuildConfig:
    """
    Load configuration (Safe version).
    """
    if config_file:
        config = BuildConfig.from_yaml(config_file)
    else:
        # Try to load default configs
        # We assume we are in adibuild/cli/mcp_server.py, so go up 3 levels
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
                raise ConfigurationError(
                    "No configuration file found and no default available."
                )

    # Apply tag override
    if tag:
        config.set("tag", tag)

    return config


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
    project: str = None,
    carrier: str = None,
    platform: str = None,
    arch: str = "unknown",
    tag: str = None,
    output: str = None,
    clean: bool = False,
    jobs: int = None,
    ignore_version_check: bool = False,
    generate_script: bool = False,
    tool_version: str = None,
) -> str:
    """Build an HDL project.

    Args:
        project: HDL project name (e.g. fmcomms2). Required if platform not set.
        carrier: Carrier board name (e.g. zed). Required if platform not set.
        platform: Target platform/build config (e.g. zed_fmcomms2). Alternative to project/carrier.
        arch: Architecture (e.g. arm, arm64)
        tag: Git tag or branch to build (auto-detects tool version)
        output: Output directory
        clean: Whether to clean before building
        jobs: Number of parallel jobs
        ignore_version_check: Ignore Vivado version check
        generate_script: Generate bash script instead of executing build
        tool_version: Override Vivado version (e.g., 2023.2)
    """
    try:
        if not platform and not (project and carrier):
            return "Error: You must specify either platform OR both project and carrier"

        if platform and (project or carrier):
            return "Error: Specify platform OR project/carrier, not both"

        # Derive tool version from tag if not explicitly specified
        if not tool_version and tag:
            detected_version = tag_to_tool_version(tag)
            if detected_version:
                tool_version = detected_version

        # Load minimal config or build dynamic one
        config_data = {"build": {"output_dir": "build"}}
        if output:
            config_data["build"]["output_dir"] = output
        if jobs:
            config_data["build"]["parallel_jobs"] = jobs

        config = BuildConfig(config_data)

        if not platform:
            platform = f"{carrier}_{project}"
            # Inject config for this synthetic platform
            platform_config = {
                "hdl_project": project,
                "carrier": carrier,
                "arch": arch,
                "name": platform,
            }
            if tool_version:
                platform_config["tool_version"] = tool_version
            config.set(f"platforms.{platform}", platform_config)

        # If platform provided, we might need a better config loading strategy if it relies on files
        # But for now let's assume if 'platform' is passed, it might be looking for a file,
        # OR we just treat it as a name if we had a way to load it.
        # Existing CLI loads config file.
        # Let's support loading config if platform is named but not dynamic.
        if platform and not (project and carrier):
            # Try to load config if we can
            try:
                loaded_config = _load_config(None, platform, tag)
                # Merge relevant overrides
                if output:
                    loaded_config.set("build.output_dir", output)
                if jobs:
                    loaded_config.set("build.parallel_jobs", jobs)
                config = loaded_config
            except Exception:
                # If load fails, maybe it was meant to be a simple dynamic build but user passed -p?
                # No, if user passes -p zed_fmcomms2, they expect it to be defined in config.
                pass

        platform_obj = _get_platform_instance(config, platform)
        builder = HDLBuilder(config, platform_obj, script_mode=generate_script)

        result = builder.build(
            clean_before=clean, ignore_version_check=ignore_version_check
        )

        if generate_script:
            return f"Script generated: {result}"

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
        return get_simpleimage_presets(tag, carrier)
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def build_linux_platform(
    platform: str,
    tag: str = None,
    config_path: str = None,
    clean: bool = False,
    defconfig: str = None,
    output: str = None,
    dtbs_only: bool = False,
    jobs: int = None,
    generate_script: bool = False,
    simpleimage_targets: list[str] = None,
    tool_version: str = None,
    allow_any_vivado: bool = False,
) -> str:
    """Build Linux kernel for a specific platform.

    Args:
        platform: Target platform (e.g., zynq, zynqmp, microblaze)
        tag: Git tag or branch to build
        config_path: Path to configuration file
        clean: Whether to clean before building
        defconfig: Override defconfig
        output: Output directory
        dtbs_only: Build only device tree blobs
        jobs: Number of parallel jobs
        generate_script: Generate bash script instead of executing build
        simpleimage_targets: List of simpleImage targets for MicroBlaze builds
        tool_version: Override toolchain version (e.g., 2023.2)
        allow_any_vivado: Allow any Vivado version instead of requiring exact match
    """
    try:
        if simpleimage_targets and platform.lower() != "microblaze":
            return (
                "Error: simpleimage_targets is only valid for MicroBlaze platform builds"
            )

        # Derive tool version from tag if not explicitly specified
        if not tool_version and tag:
            detected_version = tag_to_tool_version(tag)
            if detected_version:
                tool_version = detected_version

        config = _load_config(config_path, platform, tag)

        if jobs:
            config.set("build.parallel_jobs", jobs)

        if output:
            config.set("build.output_dir", output)

        platform_config = config.get_platform(platform)

        if defconfig:
            platform_config["defconfig"] = defconfig

        if simpleimage_targets:
            platform_config["simpleimage_targets"] = simpleimage_targets
            platform_config["kernel_target"] = simpleimage_targets[0]

        if tool_version:
            platform_config["tool_version"] = tool_version
            platform_config["strict_version"] = not allow_any_vivado

        config.set(f"platforms.{platform}", platform_config)

        platform_obj = _get_platform_instance(config, platform)
        builder = LinuxBuilder(config, platform_obj, script_mode=generate_script)

        result = builder.build(clean_before=clean, dtbs_only=dtbs_only)

        if generate_script:
            return f"Script generated: {result}"

        return f"Linux Build completed. Output: {result.get('output_dir', 'unknown')}"
    except Exception as e:
        return f"Build failed: {str(e)}"


@mcp.tool()
def configure_linux_platform(
    platform: str,
    tag: str = None,
    config_path: str = None,
    defconfig: str = None,
) -> str:
    """Configure kernel without building.

    Args:
        platform: Target platform (e.g., zynq, zynqmp, microblaze)
        tag: Git tag or branch
        config_path: Path to configuration file
        defconfig: Override defconfig
    """
    try:
        config = _load_config(config_path, platform, tag)

        if defconfig:
            platform_config = config.get_platform(platform)
            platform_config["defconfig"] = defconfig
            config.set(f"platforms.{platform}", platform_config)

        platform_obj = _get_platform_instance(config, platform)
        builder = LinuxBuilder(config, platform_obj)

        builder.prepare_source()
        builder.configure()

        return "Kernel configured successfully"
    except Exception as e:
        return f"Configuration failed: {str(e)}"


@mcp.tool()
def build_linux_dtbs(
    platform: str,
    dtb_files: list[str] = None,
    tag: str = None,
    config_path: str = None,
) -> str:
    """Build specific device tree blobs.

    Args:
        platform: Target platform (e.g., zynq, zynqmp, microblaze)
        dtb_files: List of specific DTB files to build (optional, builds all if empty)
        tag: Git tag or branch
        config_path: Path to configuration file
    """
    try:
        config = _load_config(config_path, platform, tag)
        platform_obj = _get_platform_instance(config, platform)
        builder = LinuxBuilder(config, platform_obj)

        builder.prepare_source()
        builder.configure()

        built_dtbs = builder.build_dtbs(dtbs=dtb_files)
        return f"Built {len(built_dtbs)} DTBs successfully"
    except Exception as e:
        return f"DTB build failed: {str(e)}"


@mcp.tool()
def clean_linux_platform(
    platform: str,
    tag: str = None,
    config_path: str = None,
    deep: bool = False,
) -> str:
    """Clean kernel build artifacts.

    Args:
        platform: Target platform (e.g., zynq, zynqmp, microblaze)
        tag: Git tag or branch
        config_path: Path to configuration file
        deep: Use mrproper instead of distclean (removes everything including .config)
    """
    try:
        config = _load_config(config_path, platform, tag)
        platform_obj = _get_platform_instance(config, platform)
        builder = LinuxBuilder(config, platform_obj)

        builder.prepare_source()
        builder.clean(deep=deep)

        return "Clean completed"
    except Exception as e:
        return f"Clean failed: {str(e)}"


@mcp.tool()
def list_toolchains(platform: str = None) -> dict:
    """Detect and display available toolchains.

    Args:
        platform: Optional platform to show specific selection for

    Returns:
        Dictionary containing detected toolchains and optional selection
    """
    try:
        result = {}

        # Check Vivado
        vivado = VivadoToolchain()
        vivado_info = vivado.detect()
        if vivado_info:
            result["vivado"] = {
                "version": vivado_info.version,
                "path": str(vivado_info.path),
            }

        # Check ARM GNU
        arm = ArmToolchain()
        arm_info = arm.detect()
        if arm_info:
            result["arm_gnu"] = {"version": arm_info.version, "path": str(arm_info.path)}

        # Check System
        system = SystemToolchain()
        system_info = system.detect()
        if system_info:
            result["system"] = {
                "version": system_info.version,
                "path": str(system_info.path),
            }

        if platform:
            # We need a config to get the platform instance and check what it selects
            try:
                config = _load_config(None, platform)
                platform_obj = _get_platform_instance(config, platform)
                selected = platform_obj.get_toolchain()
                result["selected_for_platform"] = {
                    "platform": platform,
                    "type": selected.type,
                    "version": selected.version,
                    "path": str(selected.path),
                }
            except Exception as e:
                result["selected_for_platform_error"] = str(e)

        return result
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def validate_configuration(config_file: str) -> str:
    """Validate configuration file against schema.

    Args:
        config_file: Path to configuration file
    """
    try:
        schema_path = (
            Path(__file__).parent.parent.parent
            / "configs"
            / "schema"
            / "linux_config.schema.json"
        )

        if not schema_path.exists():
            return f"Error: Schema file not found: {schema_path}"

        config = BuildConfig.from_yaml(config_file)
        config.validate(schema_path)
        return f"Configuration valid: {config_file}"
    except Exception as e:
        return f"Configuration validation failed: {str(e)}"
