"""Input validation utilities."""

import re
import shutil
from pathlib import Path
from typing import List, Optional

from adibuild.utils.logger import get_logger

logger = get_logger("adibuild.validators")


class ValidationError(Exception):
    """Exception raised for validation errors."""

    pass


def validate_platform(platform: str, valid_platforms: Optional[List[str]] = None) -> str:
    """
    Validate platform name.

    Args:
        platform: Platform name to validate
        valid_platforms: Optional list of valid platform names

    Returns:
        Validated platform name

    Raises:
        ValidationError: If platform is invalid
    """
    if not platform or not isinstance(platform, str):
        raise ValidationError(f"Platform must be a non-empty string, got: {platform}")

    platform = platform.lower().strip()

    if valid_platforms and platform not in valid_platforms:
        raise ValidationError(
            f"Invalid platform '{platform}'. Valid platforms: {', '.join(valid_platforms)}"
        )

    return platform


def validate_tag(tag: str) -> str:
    """
    Validate git tag format.

    Args:
        tag: Git tag to validate

    Returns:
        Validated tag

    Raises:
        ValidationError: If tag format is invalid
    """
    if not tag or not isinstance(tag, str):
        raise ValidationError(f"Tag must be a non-empty string, got: {tag}")

    tag = tag.strip()

    # Basic tag format validation (alphanumeric, dots, underscores, hyphens)
    if not re.match(r"^[a-zA-Z0-9._-]+$", tag):
        raise ValidationError(
            f"Invalid tag format '{tag}'. Tags must contain only "
            "alphanumeric characters, dots, underscores, or hyphens."
        )

    return tag


def validate_path(path: Path, must_exist: bool = False, must_be_dir: bool = False) -> Path:
    """
    Validate file system path.

    Args:
        path: Path to validate
        must_exist: If True, path must exist
        must_be_dir: If True, path must be a directory

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path validation fails
    """
    if not isinstance(path, Path):
        try:
            path = Path(path)
        except Exception as e:
            raise ValidationError(f"Invalid path: {e}") from e

    if must_exist and not path.exists():
        raise ValidationError(f"Path does not exist: {path}")

    if must_be_dir and path.exists() and not path.is_dir():
        raise ValidationError(f"Path is not a directory: {path}")

    return path


def validate_tool_available(tool: str, error_msg: Optional[str] = None) -> bool:
    """
    Validate that a required tool is available on the system.

    Args:
        tool: Tool name to check
        error_msg: Optional custom error message

    Returns:
        True if tool is available

    Raises:
        ValidationError: If tool is not found
    """
    if not shutil.which(tool):
        msg = error_msg or f"Required tool '{tool}' not found in PATH"
        raise ValidationError(msg)
    return True


def validate_tools_available(tools: List[str]) -> bool:
    """
    Validate that multiple required tools are available.

    Args:
        tools: List of tool names to check

    Returns:
        True if all tools are available

    Raises:
        ValidationError: If any tool is not found
    """
    missing = []
    for tool in tools:
        if not shutil.which(tool):
            missing.append(tool)

    if missing:
        raise ValidationError(
            f"Required tools not found in PATH: {', '.join(missing)}. "
            "Please install these tools before continuing."
        )

    return True


def validate_build_environment() -> None:
    """
    Validate that the build environment has all required tools.

    Raises:
        ValidationError: If required tools are missing
    """
    required_tools = ["make", "gcc", "git"]
    validate_tools_available(required_tools)
    logger.debug("Build environment validation passed")


def validate_cross_compile_prefix(prefix: str) -> str:
    """
    Validate cross-compile prefix and check if compiler is available.

    Args:
        prefix: Cross-compile prefix (e.g., 'arm-linux-gnueabihf-')

    Returns:
        Validated prefix

    Raises:
        ValidationError: If compiler is not found
    """
    if not prefix:
        raise ValidationError("Cross-compile prefix cannot be empty")

    compiler = f"{prefix}gcc"
    if not shutil.which(compiler):
        raise ValidationError(
            f"Cross-compiler '{compiler}' not found in PATH. "
            "Please install the appropriate toolchain."
        )

    return prefix


def validate_defconfig(defconfig: str) -> str:
    """
    Validate kernel defconfig name.

    Args:
        defconfig: Defconfig name to validate

    Returns:
        Validated defconfig name

    Raises:
        ValidationError: If defconfig format is invalid
    """
    if not defconfig or not isinstance(defconfig, str):
        raise ValidationError(f"Defconfig must be a non-empty string, got: {defconfig}")

    defconfig = defconfig.strip()

    # Should end with _defconfig
    if not defconfig.endswith("_defconfig"):
        logger.warning(
            f"Defconfig '{defconfig}' doesn't end with '_defconfig'. "
            "This may be intentional but is unusual."
        )

    return defconfig
