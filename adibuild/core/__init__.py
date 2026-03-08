"""Core functionality for adibuild."""

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.docker import (
    DockerError,
    DockerExecutionConfig,
    VivadoDockerImageManager,
    container_vivado_toolchain,
    default_vivado_image_tag,
)
from adibuild.core.executor import BuildExecutor, ExecutionResult
from adibuild.core.toolchain import Toolchain, ToolchainInfo
from adibuild.core.vivado import (
    VivadoCredentials,
    VivadoInstaller,
    VivadoInstallRequest,
    VivadoInstallResult,
    VivadoRelease,
)

__all__ = [
    "BuilderBase",
    "BuildConfig",
    "DockerError",
    "DockerExecutionConfig",
    "BuildExecutor",
    "ExecutionResult",
    "Toolchain",
    "ToolchainInfo",
    "VivadoDockerImageManager",
    "VivadoCredentials",
    "VivadoInstallRequest",
    "VivadoInstallResult",
    "VivadoInstaller",
    "VivadoRelease",
    "container_vivado_toolchain",
    "default_vivado_image_tag",
]
