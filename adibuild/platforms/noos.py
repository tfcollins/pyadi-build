"""no-OS bare-metal firmware platform configuration."""

from pathlib import Path

from adibuild.core.toolchain import ToolchainInfo, select_toolchain
from adibuild.platforms.base import Platform, PlatformError

# Maps noos_platform name -> preferred toolchain type
NOOS_PLATFORM_TOOLCHAIN = {
    "xilinx": "vivado",
    "stm32": "bare_metal",
    "linux": "system",
    "altera": "system",
    "aducm3029": "bare_metal",
    "maxim": "bare_metal",
    "pico": "bare_metal",
}

VALID_NOOS_PLATFORMS = list(NOOS_PLATFORM_TOOLCHAIN.keys())


class NoOSPlatform(Platform):
    """Platform for no-OS bare-metal firmware projects."""

    @property
    def noos_platform(self) -> str:
        """Get no-OS target platform name (e.g., 'xilinx', 'stm32')."""
        p = self.config.get("noos_platform")
        if not p:
            raise PlatformError("'noos_platform' not specified in platform configuration")
        if p not in VALID_NOOS_PLATFORMS:
            raise PlatformError(
                f"Invalid noos_platform '{p}'. Valid platforms: {VALID_NOOS_PLATFORMS}"
            )
        return p

    @property
    def noos_project(self) -> str:
        """Get no-OS project name (subdirectory under projects/)."""
        p = self.config.get("noos_project")
        if not p:
            raise PlatformError("'noos_project' not specified in platform configuration")
        return p

    @property
    def hardware_file(self) -> Path | None:
        """Get hardware file path (.xsa for Xilinx, .ioc for STM32), or None."""
        hw = self.config.get("hardware_file")
        return Path(hw) if hw else None

    @property
    def profile(self) -> str | None:
        """Get optional hardware profile (e.g., 'vcu118_ad9081_m8_l4')."""
        return self.config.get("profile")

    @property
    def iiod(self) -> bool:
        """Get whether to enable IIO daemon (IIOD=y)."""
        return bool(self.config.get("iiod", False))

    @property
    def make_variables(self) -> dict[str, str]:
        """Get additional make variables to pass to the build."""
        return self.config.get("make_variables", {})

    @property
    def arch(self) -> str:
        """
        Get target architecture identifier.

        Returns 'native' for the linux no-OS platform, 'bare_metal' for all others.
        Used for log file and script naming in BuilderBase.
        """
        if self.config.get("noos_platform") == "linux":
            return "native"
        return "bare_metal"

    def get_toolchain(self, tool_version: str | None = None) -> ToolchainInfo:
        """
        Get or select toolchain for this no-OS platform.

        Overrides base class to use noos_platform-specific toolchain mapping
        instead of arch-based dispatch.
        """
        if self._toolchain:
            return self._toolchain

        noos_plat = self.noos_platform
        default_tc_type = NOOS_PLATFORM_TOOLCHAIN.get(noos_plat, "system")

        toolchain_config = self.config.get("toolchain", {})
        preferred = toolchain_config.get("preferred", default_tc_type)
        fallbacks = toolchain_config.get("fallback", [])

        if not tool_version:
            tool_version = self.config.get("tool_version")
        strict_version = self.config.get("strict_version", False)

        self.logger.info(f"Selecting toolchain for no-OS platform '{noos_plat}'")
        if tool_version:
            self.logger.info(f"Preferred tool version: {tool_version}")

        self._toolchain = select_toolchain(
            preferred, fallbacks, tool_version, strict_version
        )
        return self._toolchain

    def validate_toolchain(self) -> bool:
        """
        Validate that the toolchain is suitable for this no-OS platform.

        Returns:
            True if toolchain is valid

        Raises:
            PlatformError: If toolchain is not suitable
        """
        toolchain = self.get_toolchain()
        noos_plat = self.noos_platform

        if noos_plat == "xilinx":
            if toolchain.type != "vivado":
                raise PlatformError(
                    f"no-OS xilinx platform requires a Vivado toolchain, "
                    f"got '{toolchain.type}'"
                )
        elif noos_plat in ("stm32", "aducm3029", "maxim", "pico"):
            if not toolchain.cross_compile_bare_metal:
                self.logger.warning(
                    f"no-OS '{noos_plat}' platform works best with arm-none-eabi-gcc. "
                    f"Current toolchain '{toolchain.type}' may not have a bare-metal prefix."
                )

        self.logger.info(
            f"Toolchain validation passed: {toolchain.type} v{toolchain.version}"
        )
        return True

    def get_make_env(self) -> dict[str, str]:
        """
        Get environment variables for make.

        Returns toolchain env_vars (includes XILINX_VITIS, XILINX_VIVADO, PATH, etc.).
        """
        toolchain = self.get_toolchain()
        return dict(toolchain.env_vars)

    def __repr__(self) -> str:
        """String representation."""
        noos_plat = self.config.get("noos_platform", "?")
        noos_proj = self.config.get("noos_project", "?")
        return f"NoOSPlatform(noos_platform={noos_plat}, noos_project={noos_proj})"
