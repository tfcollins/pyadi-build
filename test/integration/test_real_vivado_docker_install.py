"""Real Docker-backed Vivado installation test."""

from __future__ import annotations

import shlex
import subprocess
import sys
import uuid
from pathlib import Path

import pytest


def _emit(message: str) -> None:
    """Write progress messages to stderr so long-running steps stay visible."""
    sys.stderr.write(message + "\n")
    sys.stderr.flush()


def _run_command(
    cmd: list[str],
    cwd: Path | None = None,
    label: str = "host",
) -> subprocess.CompletedProcess:
    """Run a host-side command, streaming output for long-running Docker steps."""
    _emit(f"[{label}] $ {' '.join(shlex.quote(part) for part in cmd)}")
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines: list[str] = []
    assert process.stdout is not None
    for line in process.stdout:
        output_lines.append(line)
        sys.stderr.write(f"[{label}] {line}")
        sys.stderr.flush()

    return_code = process.wait()
    stdout = "".join(output_lines)
    if return_code != 0:
        raise AssertionError(
            f"Command failed ({return_code}): {' '.join(cmd)}\n" f"stdout:\n{stdout}"
        )
    return subprocess.CompletedProcess(cmd, return_code, stdout=stdout, stderr="")


@pytest.mark.real_build
@pytest.mark.slow
@pytest.mark.docker_vivado
class TestRealVivadoDockerInstall:
    """Real Docker-backed Vivado install coverage."""

    def test_install_vivado_in_docker_and_verify_detection(
        self,
        check_docker_available,
        check_vivado_docker_network,
        check_vivado_docker_disk_space,
        vivado_docker_credentials,
        docker_vivado_test_version,
        docker_vivado_test_install_version,
        docker_vivado_installer_bundle,
        docker_vivado_host_cache_dir,
        docker_vivado_debug_keep,
    ):
        """Install Vivado in a container and verify it is available afterwards."""
        del check_docker_available
        del check_vivado_docker_network
        del check_vivado_docker_disk_space

        repo_root = Path(__file__).resolve().parents[2]
        dockerfile = (
            repo_root
            / "test"
            / "fixtures"
            / "docker"
            / "vivado-installer-ubuntu2204.Dockerfile"
        )

        run_id = uuid.uuid4().hex[:12]
        image_tag = f"pyadi-build-vivado-test:{run_id}"
        container_name = f"pyadi-build-vivado-test-{run_id}"

        container_script = """
set -euo pipefail
echo "[container] Starting Docker Vivado install workflow"
echo "[container] Vivado version request: $VIVADO_VERSION"
echo "[container] Expected install version: $VIVADO_INSTALL_VERSION"
echo "[container] Upgrading Python packaging tools"
python3 -m pip install --upgrade pip setuptools wheel
echo "[container] Copying repository into writable workspace"
cp -a /src/. /workspace-src
cd /workspace-src
echo "[container] Installing pyadi-build with Vivado browser support"
python3 -m pip install -e '.[vivado-browser]'
echo "[container] Running Vivado installer"
INSTALL_CMD=(adibuild -v vivado install --version "$VIVADO_VERSION" --non-interactive)
if [ -n "${VIVADO_INSTALLER_PATH:-}" ]; then
  echo "[container] Using mounted installer: $VIVADO_INSTALLER_PATH"
  INSTALL_CMD+=(--installer-path "$VIVADO_INSTALLER_PATH")
fi

if [ "${ADIBUILD_BROWSER_HEADLESS:-1}" = "0" ] || [ "${ADIBUILD_BROWSER_HEADLESS:-1}" = "false" ]; then
  echo "[container] Headless mode disabled; using xvfb-run"
  xvfb-run --server-args="-screen 0 1920x1080x24" "${INSTALL_CMD[@]}"
else
  "${INSTALL_CMD[@]}"
fi
echo "[container] Verifying settings64.sh exists"
test -f "/opt/Xilinx/Vivado/$VIVADO_INSTALL_VERSION/settings64.sh"
echo "[container] Checking vivado -version output"
"/opt/Xilinx/Vivado/$VIVADO_INSTALL_VERSION/bin/vivado" -version | tee /tmp/vivado-version.txt
grep -q "Vivado" /tmp/vivado-version.txt
grep -q "$VIVADO_INSTALL_VERSION" /tmp/vivado-version.txt
echo "[container] Running adibuild vivado detect"
adibuild -v vivado detect --version "$VIVADO_VERSION" --install-dir /opt/Xilinx
echo "[container] Docker Vivado install workflow completed"
"""

        docker_run_cmd = [
            "docker",
            "run",
            "--name",
            container_name,
            "-e",
            f"AMD_USERNAME={vivado_docker_credentials['AMD_USERNAME']}",
            "-e",
            f"AMD_PASSWORD={vivado_docker_credentials['AMD_PASSWORD']}",
            "-e",
            f"VIVADO_VERSION={docker_vivado_test_version}",
            "-e",
            f"VIVADO_INSTALL_VERSION={docker_vivado_test_install_version}",
            "-e",
            f"ADIBUILD_BROWSER_HEADLESS={os.environ.get('ADIBUILD_BROWSER_HEADLESS', '1')}",
            "-v",
            f"{repo_root}:/src:ro",
            "-v",
            f"{docker_vivado_host_cache_dir}:/root/.adibuild/toolchains/vivado",
        ]

        if docker_vivado_installer_bundle["mode"] == "synthetic":
            installer_path = docker_vivado_installer_bundle["installer_path"]
            assert installer_path is not None
            _emit(
                "[docker-test] Using synthetic local Vivado installer because "
                f"{docker_vivado_installer_bundle['reason']}"
            )
            docker_run_cmd.extend(
                [
                    "-e",
                    "ADIBUILD_VIVADO_SKIP_VERIFY=1",
                    "-e",
                    f"VIVADO_INSTALLER_PATH=/installer-src/{installer_path.name}",
                    "-v",
                    f"{installer_path.parent}:/installer-src:ro",
                ]
            )

        docker_run_cmd.extend(
            [
                image_tag,
                "bash",
                "-lc",
                container_script,
            ]
        )

        try:
            _emit("[docker-test] Building Docker image for Vivado install test")
            _run_command(
                [
                    "docker",
                    "build",
                    "-t",
                    image_tag,
                    "-f",
                    str(dockerfile),
                    str(dockerfile.parent),
                ],
                label="docker-build",
            )

            _emit("[docker-test] Running Docker container for Vivado installation")
            _run_command(
                docker_run_cmd,
                label="docker-run",
            )
        finally:
            if not docker_vivado_debug_keep:
                _emit("[docker-test] Cleaning up Docker container and image")
                subprocess.run(
                    ["docker", "rm", "-f", container_name],
                    capture_output=True,
                    text=True,
                )
                subprocess.run(
                    ["docker", "rmi", "-f", image_tag],
                    capture_output=True,
                    text=True,
                )
            else:
                _emit(
                    f"[docker-test] Keeping Docker artifacts: image={image_tag}, "
                    f"container={container_name}"
                )
