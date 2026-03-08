"""Helpers for Docker-based Vivado integration tests."""

from __future__ import annotations

import os
from pathlib import Path

from adibuild.core.vivado import VivadoInstaller

DEFAULT_DOCKER_VIVADO_VERSION = "2023.2"


def docker_vivado_version() -> str:
    """Return the Vivado version to install in the Docker E2E test."""
    return os.environ.get("ADIBUILD_VIVADO_DOCKER_VERSION", DEFAULT_DOCKER_VIVADO_VERSION)


def docker_vivado_install_version(version: str | None = None) -> str:
    """Return the on-disk Vivado install directory version for a requested release."""
    requested_version = version or docker_vivado_version()
    release = VivadoInstaller().resolve_release(requested_version)
    return release.install_version


def keep_docker_vivado_artifacts() -> bool:
    """Whether to preserve Docker image/container artifacts after the test."""
    value = os.environ.get("ADIBUILD_KEEP_VIVADO_DOCKER_ARTIFACTS", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def docker_vivado_cache_dir(default_root: Path) -> Path:
    """Return the host cache directory mounted into the Docker container."""
    configured = os.environ.get("ADIBUILD_VIVADO_DOCKER_CACHE_DIR")
    if configured:
        return Path(configured).expanduser()
    return default_root / "vivado-docker-cache"


def use_synthetic_vivado_installer() -> bool:
    """Whether the Docker Vivado test should use a synthetic local installer."""
    value = os.environ.get("ADIBUILD_VIVADO_DOCKER_SYNTHETIC_INSTALLER", "")
    return value.strip().lower() in {"1", "true", "yes", "on"}


def build_synthetic_vivado_installer(version: str, root: Path) -> Path:
    """Create a tiny self-extracting installer that simulates Vivado install flow."""
    release = VivadoInstaller().resolve_release(version)
    root.mkdir(parents=True, exist_ok=True)
    installer_path = root / release.filename

    script = f"""#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target)
      TARGET_DIR="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

if [ -z "$TARGET_DIR" ]; then
  echo "missing --target" >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cat > "$TARGET_DIR/xsetup" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

MODE=""
LOCATION="/opt/Xilinx"
while [ "$#" -gt 0 ]; do
  case "$1" in
    -b)
      MODE="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    -c|--config)
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

case "$MODE" in
  AuthTokenGen)
    cat >/dev/null
    exit 0
    ;;
  Install)
    INSTALL_ROOT="$LOCATION/Vivado/{release.install_version}"
    mkdir -p "$INSTALL_ROOT/bin"
    cat > "$INSTALL_ROOT/settings64.sh" <<'EOS'
#!/usr/bin/env bash
export XILINX_VIVADO="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
export PATH="$XILINX_VIVADO/bin:$PATH"
EOS
    cat > "$INSTALL_ROOT/bin/vivado" <<'EOS'
#!/usr/bin/env bash
if [ "${{1:-}}" = "-version" ]; then
  echo "Vivado v{release.install_version} (64-bit)"
  exit 0
fi
echo "Synthetic Vivado wrapper"
EOS
    chmod +x "$INSTALL_ROOT/settings64.sh" "$INSTALL_ROOT/bin/vivado"
    exit 0
    ;;
  *)
    echo "unsupported mode: $MODE" >&2
    exit 1
    ;;
esac
EOF
chmod +x "$TARGET_DIR/xsetup"
"""
    installer_path.write_text(script)
    installer_path.chmod(0o755)
    return installer_path
