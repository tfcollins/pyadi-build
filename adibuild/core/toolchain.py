"""Toolchain detection and management."""

import os
import shutil
import subprocess
import tarfile
import tempfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import requests

from adibuild.utils.logger import get_logger


class ToolchainError(Exception):
    """Exception raised for toolchain errors."""

    pass


@dataclass
class ToolchainInfo:
    """Information about a detected toolchain."""

    type: str  # 'vivado', 'arm', 'system', 'bare_metal'
    version: str
    path: Path
    env_vars: dict[str, str]
    cross_compile_arm32: str | None = None
    cross_compile_arm64: str | None = None
    cross_compile_microblaze: str | None = None
    cross_compile_bare_metal: str | None = None


class Toolchain(ABC):
    """Abstract base class for toolchains."""

    def __init__(self):
        """Initialize toolchain."""
        self.logger = get_logger(f"adibuild.toolchain.{self.__class__.__name__}")

    @abstractmethod
    def detect(self) -> ToolchainInfo | None:
        """
        Detect if toolchain is available.

        Returns:
            ToolchainInfo if detected, None otherwise
        """
        pass

    @abstractmethod
    def get_cross_compile(self, arch: str) -> str:
        """
        Get cross-compile prefix for architecture.

        Args:
            arch: Target architecture ('arm' or 'arm64')

        Returns:
            Cross-compile prefix
        """
        pass


class VivadoToolchain(Toolchain):
    """Xilinx Vivado/Vitis toolchain."""

    # Vivado/Vitis version to GCC version mapping (for reference)
    # These GCC versions are what Vitis/Vivado ships with internally
    VIVADO_GCC_MAP = {
        "2025.1": "13.3.0",
        "2023.2": "12.2.0",
        "2023.1": "12.2.0",
        "2022.2": "11.2.0",
        "2022.1": "11.2.0",
        "2021.2": "10.2.0",
        "2021.1": "10.2.0",
    }

    def __init__(
        self,
        search_paths: list[Path] | None = None,
        preferred_version: str | None = None,
        strict_version: bool = False,
    ):
        """
        Initialize VivadoToolchain.

        Args:
            search_paths: Optional list of paths to search for Vivado/Vitis
            preferred_version: Preferred Vivado version (e.g., "2023.2")
            strict_version: If True and preferred_version set, ONLY search for that version
        """
        super().__init__()
        self.preferred_version = preferred_version
        self.strict_version = strict_version
        self.search_paths = search_paths or self._get_default_search_paths()

    def _get_default_search_paths(self) -> list[Path]:
        """Get default search paths for Vivado/Vitis."""
        paths = []

        # If strict mode with preferred version, ONLY search for that version
        if self.strict_version and self.preferred_version:
            versions = [self.preferred_version]
        else:
            versions = [
                "2025.2",
                "2025.1",
                "2024.2",
                "2024.1",
                "2023.2",
                "2023.1",
                "2022.2",
                "2022.1",
                "2021.2",
                "2021.1",
            ]
            # If preferred version specified (non-strict), search it first
            if self.preferred_version and self.preferred_version in versions:
                versions = versions.copy()
                versions.remove(self.preferred_version)
                versions.insert(0, self.preferred_version)

        for version in versions:
            paths.append(Path(f"/opt/Xilinx/Vivado/{version}"))
            paths.append(Path(f"/opt/Xilinx/Vitis/{version}"))
            paths.append(Path(f"/opt/Xilinx/{version}/Vivado"))
            paths.append(Path(f"/opt/Xilinx/{version}/Vitis"))
            paths.append(Path(f"/tools/Xilinx/{version}/Vivado"))
            paths.append(Path(f"/tools/Xilinx/{version}/Vitis"))

        # Check environment variable
        if "XILINX_VIVADO" in os.environ:
            paths.insert(0, Path(os.environ["XILINX_VIVADO"]))
        if "XILINX_VITIS" in os.environ:
            paths.insert(0, Path(os.environ["XILINX_VITIS"]))

        return paths

    def detect(self) -> ToolchainInfo | None:
        """Detect Vivado/Vitis installation."""
        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            self.logger.debug(f"Searching for Vivado/Vitis in {search_path}")

            # Find version directories
            if search_path.is_dir():
                settings_script = search_path / "settings64.sh"
                if settings_script.exists():
                    # Fine XXXX.X version from path
                    import re

                    for i in [-2, -1]:
                        version = search_path.parts[i]
                        match = re.match(r"(\d{4}\.\d)", version)
                        if match:
                            version = match.group(1)
                            break
                        else:
                            version = "unknown"
                    self.logger.info(f"Found Vivado/Vitis {version} at {search_path}")

                    # Extract environment variables
                    env_vars = self._get_env_vars(settings_script)
                    if env_vars:
                        return ToolchainInfo(
                            type="vivado",
                            version=version,
                            path=search_path,
                            env_vars=env_vars,
                            cross_compile_arm32="arm-linux-gnueabihf-",
                            cross_compile_arm64="aarch64-linux-gnu-",
                            cross_compile_microblaze="microblazeel-xilinx-linux-gnu-",
                        )

        self.logger.debug("Vivado/Vitis toolchain not found")
        return None

    def _get_env_vars(self, settings_script: Path) -> dict[str, str]:
        """
        Extract environment variables from settings64.sh.

        Args:
            settings_script: Path to settings64.sh

        Returns:
            Dictionary of environment variables
        """
        try:
            # Source the script and dump environment
            cmd = f'bash -c "source {settings_script} > /dev/null 2>&1 && env"'
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=30
            )

            if result.returncode != 0:
                self.logger.warning(f"Failed to source {settings_script}")
                return {}

            # Parse environment variables
            env_vars = {}
            for line in result.stdout.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Only keep Xilinx-related variables and PATH
                    if key.startswith("XILINX") or key == "PATH":
                        env_vars[key] = value

            return env_vars

        except (subprocess.TimeoutExpired, Exception) as e:
            self.logger.warning(
                f"Error extracting environment from {settings_script}: {e}"
            )
            return {}

    def get_cross_compile(self, arch: str) -> str:
        """Get cross-compile prefix for architecture."""
        toolchain_info = self.detect()
        if not toolchain_info:
            raise ToolchainError("Vivado toolchain not detected")

        if arch == "arm":
            return toolchain_info.cross_compile_arm32
        elif arch == "arm64":
            return toolchain_info.cross_compile_arm64
        else:
            raise ToolchainError(f"Unsupported architecture: {arch}")


class ArmToolchain(Toolchain):
    """ARM GNU toolchain with auto-download support."""

    # Vivado/Vitis version to ARM toolchain version mapping
    # Maps based on GCC version shipped with each Vitis release
    VIVADO_ARM_MAP = {
        "2025.1": "13.3.rel1",  # GCC 13.3.0
        "2023.2": "12.2.rel1",  # GCC 12.2.0
        "2023.1": "12.2.rel1",  # GCC 12.2.0
        "2022.2": "11.2-2022.02",  # GCC 11.2.0
        "2022.1": "11.2-2022.02",  # GCC 11.2.0
        "2021.2": "10.3-2021.07",  # GCC 10.2.0/10.3.0
        "2021.1": "10.3-2021.07",  # GCC 10.2.0/10.3.0
        "2020.2": "10.2-2020.11",  # GCC 10.2.0
        "2020.1": "10.2-2020.11",  # GCC 10.2.0
    }

    # URL patterns for different ARM toolchain versions
    # New versions (11.3.rel1+): gnu/ path + arm-gnu-toolchain- prefix
    # Transition version (11.2-2022.02): gnu/ path + gcc-arm- prefix
    # Old versions (10.x): gnu-a/ path + gcc-arm- prefix
    ARM_URL_PATTERNS = {
        # (base_path, file_prefix, extract_prefix)
        "new": ("gnu", "arm-gnu-toolchain", "arm-gnu-toolchain"),
        "transition": ("gnu", "gcc-arm", "gcc-arm"),
        "old": ("gnu-a", "gcc-arm", "gcc-arm"),
    }

    # Versions that use each URL pattern
    OLD_VERSIONS = ["10.2-2020.11", "10.3-2021.07"]
    TRANSITION_VERSIONS = ["11.2-2022.02"]

    # Base URLs for ARM downloads (primary and fallback)
    ARM_BASE_URLS = [
        "https://armkeil.blob.core.windows.net/developer/Files/downloads/",
        "https://developer.arm.com/-/media/Files/downloads/",
    ]

    def __init__(self, cache_dir: Path | None = None, version: str | None = None):
        """
        Initialize ArmToolchain.

        Args:
            cache_dir: Directory to cache downloaded toolchains
            version: Specific ARM toolchain version to use
        """
        super().__init__()
        self.cache_dir = cache_dir or Path.home() / ".adibuild" / "toolchains" / "arm"
        self.version = version
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def detect(self) -> ToolchainInfo | None:
        """Detect installed ARM toolchain."""
        # Check cache directory for installed toolchains
        if not self.cache_dir.exists():
            return None

        # Look for ARM32 and ARM64 toolchains
        # New versions use: arm-gnu-toolchain-{version}-x86_64-{target}
        # Old versions use: gcc-arm-{version}-x86_64-{target}
        arm32_dirs = list(
            self.cache_dir.glob("arm-gnu-toolchain-*-x86_64-arm-none-linux-gnueabihf")
        ) + list(self.cache_dir.glob("gcc-arm-*-x86_64-arm-none-linux-gnueabihf"))
        arm64_dirs = list(
            self.cache_dir.glob("arm-gnu-toolchain-*-x86_64-aarch64-none-linux-gnu")
        ) + list(self.cache_dir.glob("gcc-arm-*-x86_64-aarch64-none-linux-gnu"))

        if arm32_dirs or arm64_dirs:
            # Use the most recent version
            all_dirs = arm32_dirs + arm64_dirs
            latest = max(all_dirs, key=lambda p: p.name)

            # Extract version from directory name
            version = self._extract_version(latest.name)

            self.logger.info(f"Found ARM GNU toolchain version {version} in cache")

            # Build PATH with both toolchains
            path_additions = []
            for tc_dir in arm32_dirs:
                path_additions.append(str(tc_dir / "bin"))
            for tc_dir in arm64_dirs:
                path_additions.append(str(tc_dir / "bin"))

            env_vars = {
                "PATH": ":".join(path_additions) + ":" + os.environ.get("PATH", "")
            }

            return ToolchainInfo(
                type="arm",
                version=version,
                path=self.cache_dir,
                env_vars=env_vars,
                cross_compile_arm32="arm-none-linux-gnueabihf-",
                cross_compile_arm64="aarch64-none-linux-gnu-",
            )

        return None

    def download(self, vivado_version: str | None = None) -> ToolchainInfo:
        """
        Download ARM GNU toolchain.

        Args:
            vivado_version: Vivado version to map to ARM toolchain version

        Returns:
            ToolchainInfo for downloaded toolchain

        Raises:
            ToolchainError: If download fails
        """
        # Determine ARM toolchain version
        if self.version:
            arm_version = self.version
        elif vivado_version and vivado_version in self.VIVADO_ARM_MAP:
            arm_version = self.VIVADO_ARM_MAP[vivado_version]
        else:
            # Default to latest known good version
            arm_version = "12.2.rel1"

        self.logger.info(f"Downloading ARM GNU toolchain version {arm_version}")

        # Download both ARM32 and ARM64 toolchains
        arm32_dir = self._download_toolchain(arm_version, "arm-none-linux-gnueabihf")
        arm64_dir = self._download_toolchain(arm_version, "aarch64-none-linux-gnu")

        # Build PATH
        path_additions = [
            str(arm32_dir / "bin"),
            str(arm64_dir / "bin"),
        ]

        env_vars = {"PATH": ":".join(path_additions) + ":" + os.environ.get("PATH", "")}

        return ToolchainInfo(
            type="arm",
            version=arm_version,
            path=self.cache_dir,
            env_vars=env_vars,
            cross_compile_arm32="arm-none-linux-gnueabihf-",
            cross_compile_arm64="aarch64-none-linux-gnu-",
        )

    def _get_url_pattern(self, version: str) -> tuple[str, str, str]:
        """
        Get URL pattern for a specific ARM toolchain version.

        Args:
            version: ARM toolchain version (e.g., '12.2.rel1')

        Returns:
            Tuple of (base_path, file_prefix, extract_prefix)
        """
        if version in self.OLD_VERSIONS:
            return self.ARM_URL_PATTERNS["old"]
        elif version in self.TRANSITION_VERSIONS:
            return self.ARM_URL_PATTERNS["transition"]
        else:
            return self.ARM_URL_PATTERNS["new"]

    def _download_toolchain(self, version: str, target: str) -> Path:
        """
        Download specific ARM GNU toolchain.

        Args:
            version: ARM toolchain version (e.g., '12.2.rel1')
            target: Target triple (e.g., 'arm-none-linux-gnueabihf')

        Returns:
            Path to extracted toolchain

        Raises:
            ToolchainError: If download fails
        """
        # Get URL pattern for this version
        base_path, file_prefix, extract_prefix = self._get_url_pattern(version)

        # Build filename and URL
        # Format: {file_prefix}-{version}-x86_64-{target}.tar.xz
        filename = f"{file_prefix}-{version}-x86_64-{target}.tar.xz"

        # URL structure: {base}/{base_path}/{version}/binrel/{filename}
        # Try multiple base URLs in case one is down
        urls = [
            f"{base_url}{base_path}/{version}/binrel/{filename}"
            for base_url in self.ARM_BASE_URLS
        ]

        extract_dir = self.cache_dir / f"{extract_prefix}-{version}-x86_64-{target}"

        # Check if already downloaded
        if extract_dir.exists():
            self.logger.info(f"Toolchain already exists at {extract_dir}")
            return extract_dir

        # Try each URL until one succeeds
        last_error = None
        for url in urls:
            self.logger.info(f"Downloading from {url}")

            try:
                # Download to temporary file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=".tar.xz"
                ) as tmp_file:
                    response = requests.get(url, stream=True, timeout=300)
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    for chunk in response.iter_content(chunk_size=8192):
                        tmp_file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            self.logger.debug(f"Download progress: {percent:.1f}%")

                    tmp_path = Path(tmp_file.name)

                # Extract
                self.logger.info(f"Extracting to {self.cache_dir}")
                with tarfile.open(tmp_path, "r:xz") as tar:
                    tar.extractall(self.cache_dir)

                # Clean up
                tmp_path.unlink()

                self.logger.info(f"Successfully installed toolchain to {extract_dir}")
                return extract_dir

            except requests.RequestException as e:
                last_error = e
                self.logger.warning(f"Failed to download from {url}: {e}")
                continue
            except tarfile.TarError as e:
                last_error = e
                raise ToolchainError(f"Failed to extract toolchain: {e}") from e

        # If we get here, all URLs failed
        raise ToolchainError(
            f"Failed to download toolchain from any source. Last error: {last_error}"
        ) from last_error

    def _extract_version(self, dirname: str) -> str:
        """Extract version from directory name."""
        # Handle both naming formats:
        # New: arm-gnu-toolchain-{version}-x86_64-{target}
        #      e.g., arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu
        # Old: gcc-arm-{version}-x86_64-{target}
        #      e.g., gcc-arm-11.2-2022.02-x86_64-arm-none-linux-gnueabihf
        parts = dirname.split("-")
        if dirname.startswith("arm-gnu-toolchain-") and len(parts) >= 4:
            # New format: version is at index 3
            return parts[3]
        elif dirname.startswith("gcc-arm-") and len(parts) >= 3:
            # Old format: version is at index 2, but may contain hyphens (e.g., 11.2-2022.02)
            # Find x86_64 to determine where version ends
            try:
                x86_idx = parts.index("x86_64")
                version_parts = parts[2:x86_idx]
                return "-".join(version_parts)
            except ValueError:
                return parts[2]
        return "unknown"

    def get_cross_compile(self, arch: str) -> str:
        """Get cross-compile prefix for architecture."""
        if arch == "arm":
            return "arm-none-linux-gnueabihf-"
        elif arch == "arm64":
            return "aarch64-none-linux-gnu-"
        else:
            raise ToolchainError(f"Unsupported architecture: {arch}")


class SystemToolchain(Toolchain):
    """System-installed cross-compiler toolchain."""

    def detect(self) -> ToolchainInfo | None:
        """Detect system-installed cross-compilers."""
        arm32_gcc = shutil.which("arm-linux-gnueabihf-gcc")
        arm64_gcc = shutil.which("aarch64-linux-gnu-gcc")

        if not arm32_gcc and not arm64_gcc:
            return None

        # Get versions
        version = "system"
        if arm32_gcc:
            version = self._get_gcc_version(arm32_gcc)
        elif arm64_gcc:
            version = self._get_gcc_version(arm64_gcc)

        self.logger.info(f"Found system toolchain (GCC {version})")

        return ToolchainInfo(
            type="system",
            version=version,
            path=Path("/usr"),
            env_vars={},
            cross_compile_arm32="arm-linux-gnueabihf-" if arm32_gcc else None,
            cross_compile_arm64="aarch64-linux-gnu-" if arm64_gcc else None,
        )

    def _get_gcc_version(self, gcc_path: str) -> str:
        """Get GCC version."""
        try:
            result = subprocess.run(
                [gcc_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Parse version from first line
                first_line = result.stdout.splitlines()[0]
                # Look for version pattern (e.g., '9.4.0')
                import re

                match = re.search(r"(\d+\.\d+\.\d+)", first_line)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return "unknown"

    def get_cross_compile(self, arch: str) -> str:
        """Get cross-compile prefix for architecture."""
        toolchain_info = self.detect()
        if not toolchain_info:
            raise ToolchainError("System toolchain not detected")

        if arch == "arm":
            if not toolchain_info.cross_compile_arm32:
                raise ToolchainError("ARM32 cross-compiler not found in system")
            return toolchain_info.cross_compile_arm32
        elif arch == "arm64":
            if not toolchain_info.cross_compile_arm64:
                raise ToolchainError("ARM64 cross-compiler not found in system")
            return toolchain_info.cross_compile_arm64
        else:
            raise ToolchainError(f"Unsupported architecture: {arch}")


class BareMetalToolchain(Toolchain):
    """Bare-metal ARM toolchain (arm-none-eabi-gcc from system PATH)."""

    def detect(self) -> ToolchainInfo | None:
        """Detect system-installed arm-none-eabi-gcc."""
        gcc = shutil.which("arm-none-eabi-gcc")
        if not gcc:
            return None

        version = self._get_gcc_version(gcc)
        self.logger.info(f"Found bare-metal toolchain (arm-none-eabi-gcc {version})")
        return ToolchainInfo(
            type="bare_metal",
            version=version,
            path=Path(gcc).parent.parent,
            env_vars={},
            cross_compile_bare_metal="arm-none-eabi-",
        )

    def _get_gcc_version(self, gcc_path: str) -> str:
        """Get GCC version."""
        try:
            result = subprocess.run(
                [gcc_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                first_line = result.stdout.splitlines()[0]
                import re

                match = re.search(r"(\d+\.\d+\.\d+)", first_line)
                if match:
                    return match.group(1)
        except Exception:
            pass
        return "unknown"

    def get_cross_compile(self, arch: str) -> str:
        """Get cross-compile prefix for architecture."""
        if arch in ("arm", "bare_metal"):
            return "arm-none-eabi-"
        raise ToolchainError(f"BareMetalToolchain does not support arch: {arch}")


def select_toolchain(
    preferred: str = "vivado",
    fallbacks: list[str] | None = None,
    tool_version: str | None = None,
    strict_version: bool = False,
) -> ToolchainInfo:
    """
    Select and return best available toolchain.

    Args:
        preferred: Preferred toolchain type
        fallbacks: List of fallback toolchain types
        tool_version: Preferred tool version (e.g., "2023.2") for Vivado/ARM toolchain
        strict_version: If True and tool_version set, only accept exact Vivado version match

    Returns:
        ToolchainInfo for selected toolchain

    Raises:
        ToolchainError: If no suitable toolchain found
    """
    logger = get_logger("adibuild.toolchain")
    if fallbacks is None:
        fallbacks = ["arm", "system"]

    # Try preferred toolchain first
    toolchain_types = [preferred] + [fb for fb in fallbacks if fb != preferred]

    for tc_type in toolchain_types:
        logger.info(f"Trying {tc_type} toolchain...")

        try:
            if tc_type == "vivado":
                tc = VivadoToolchain(
                    preferred_version=tool_version,
                    strict_version=strict_version,
                )
                info = tc.detect()
                if info:
                    logger.info(f"Selected Vivado toolchain version {info.version}")
                    return info

            elif tc_type == "arm":
                tc = ArmToolchain()
                info = tc.detect()
                if info:
                    logger.info(f"Selected ARM GNU toolchain version {info.version}")
                    return info
                else:
                    # Try to download
                    logger.info("ARM GNU toolchain not found, downloading...")
                    info = tc.download(tool_version)
                    logger.info(
                        f"Downloaded and selected ARM GNU toolchain version {info.version}"
                    )
                    return info

            elif tc_type == "system":
                tc = SystemToolchain()
                info = tc.detect()
                if info:
                    logger.info(f"Selected system toolchain version {info.version}")
                    return info

            elif tc_type == "bare_metal":
                tc = BareMetalToolchain()
                info = tc.detect()
                if info:
                    logger.info(f"Selected bare-metal toolchain version {info.version}")
                    return info

        except Exception as e:
            logger.warning(f"Failed to use {tc_type} toolchain: {e}")
            continue

    raise ToolchainError(
        f"No suitable toolchain found. Tried: {', '.join(toolchain_types)}. "
        "Please install a cross-compiler toolchain or Xilinx Vivado/Vitis."
    )
