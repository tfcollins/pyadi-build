"""Platform for userspace library builds (CMake-based)."""

import shutil
from pathlib import Path

from adibuild.core.toolchain import ToolchainInfo, select_toolchain
from adibuild.platforms.base import Platform, PlatformError

# Arch → cmake CMAKE_SYSTEM_PROCESSOR value
ARCH_TO_CMAKE_PROCESSOR = {
    "arm": "arm",
    "arm64": "aarch64",
    "native": None,
}

# Arch → default cross-compiler prefix
DEFAULT_CROSS_COMPILE = {
    "arm": "arm-linux-gnueabihf-",
    "arm64": "aarch64-linux-gnu-",
    "native": "",
}

VALID_LIB_ARCHS = list(ARCH_TO_CMAKE_PROCESSOR.keys())


class LibPlatform(Platform):
    """
    Platform for userspace library builds using CMake.

    Supports native and cross-compiled builds for arm/arm64 targets.
    Cross-compilation is configured via CMake variables rather than
    environment variables, so cmake handles the compiler selection
    directly.

    Config keys:
        arch (str): Target architecture - one of ``arm``, ``arm64``, ``native``.
            Defaults to ``native``.
        cross_compile (str, optional): Cross-compiler prefix override, e.g.
            ``arm-linux-gnueabihf-``. Inferred from arch if not provided.
        libiio_path (str, optional): Path to cross-compiled libiio installation
            (must contain ``include/`` and ``lib/`` subdirs).
        sysroot (str, optional): CMake sysroot path for cross builds.
        cmake_options (dict, optional): Extra ``-D`` cmake options, e.g.
            ``{BUILD_SHARED_LIBS: "OFF"}``.
        toolchain (dict, optional): Toolchain preferences ``{preferred, fallback}``.
    """

    def __init__(self, config: dict):
        super().__init__(config)
        arch = config.get("arch", "native")
        if arch not in VALID_LIB_ARCHS:
            raise PlatformError(
                f"Unsupported arch '{arch}'. Valid options: {VALID_LIB_ARCHS}"
            )

    @property
    def arch(self) -> str:
        """Target architecture (arm / arm64 / native)."""
        return self.config.get("arch", "native")

    @property
    def cross_compile(self) -> str:
        """Cross-compiler prefix (empty string for native builds)."""
        return self.config.get("cross_compile", DEFAULT_CROSS_COMPILE.get(self.arch, ""))

    @property
    def cmake_processor(self) -> str | None:
        """CMake CMAKE_SYSTEM_PROCESSOR value, or None for native."""
        return ARCH_TO_CMAKE_PROCESSOR.get(self.arch)

    @property
    def libiio_path(self) -> Path | None:
        """Path to cross-compiled libiio, or None if not specified."""
        path = self.config.get("libiio_path")
        return Path(path) if path else None

    @property
    def sysroot(self) -> Path | None:
        """CMake sysroot path, or None if not specified."""
        path = self.config.get("sysroot")
        return Path(path) if path else None

    @property
    def cmake_options(self) -> dict[str, str]:
        """Extra cmake -D options from config."""
        return self.config.get("cmake_options", {})

    def get_cmake_args(self) -> list[str]:
        """
        Build the list of cmake ``-D`` arguments for cross-compilation.

        Returns:
            List of cmake arguments (e.g. ``["-DCMAKE_C_COMPILER=...", ".."]``).
            Does not include the source path argument — that is added by the builder.
        """
        args: list[str] = []

        if self.arch != "native" and self.cross_compile:
            args += [
                f"-DCMAKE_C_COMPILER={self.cross_compile}gcc",
                f"-DCMAKE_CXX_COMPILER={self.cross_compile}g++",
                "-DCMAKE_SYSTEM_NAME=Linux",
            ]
            if self.cmake_processor:
                args.append(f"-DCMAKE_SYSTEM_PROCESSOR={self.cmake_processor}")

        if self.sysroot:
            args.append(f"-DCMAKE_SYSROOT={self.sysroot}")

        for key, value in self.cmake_options.items():
            args.append(f"-D{key}={value}")

        return args

    def get_make_env(self) -> dict[str, str]:
        """
        Return environment variables for make.

        For CMake-based builds the compiler is set via cmake arguments rather
        than environment variables, so this returns an empty dict.
        """
        return {}

    def get_toolchain(self, tool_version: str | None = None) -> ToolchainInfo:
        """
        Select a system toolchain.

        CMake library builds drive the compiler via cmake variables, so we
        only need a lightweight system toolchain to satisfy the base class
        contract and provide environment variables if needed.
        """
        if self._toolchain:
            return self._toolchain

        tc_config = self.config.get("toolchain", {})
        preferred = tc_config.get("preferred", "system")
        fallbacks = tc_config.get("fallback", [])
        self._toolchain = select_toolchain(preferred, fallbacks)
        return self._toolchain

    def validate_toolchain(self) -> bool:
        """
        Validate that the cross-compiler is present (for cross builds).

        Raises:
            PlatformError: If the cross-compiler is not found in PATH.
        """
        if self.arch != "native" and self.cross_compile:
            gcc_name = f"{self.cross_compile}gcc"
            if not shutil.which(gcc_name):
                raise PlatformError(
                    f"Cross-compiler '{gcc_name}' not found in PATH. "
                    f"Install the appropriate cross-toolchain for '{self.arch}'."
                )
        self.logger.info(f"Toolchain validation passed for arch={self.arch!r}")
        return True

    def __repr__(self) -> str:
        return (
            f"LibPlatform(arch={self.arch!r}, " f"cross_compile={self.cross_compile!r})"
        )
