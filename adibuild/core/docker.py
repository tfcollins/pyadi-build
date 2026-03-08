"""Docker execution and reusable Vivado image management."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from adibuild.core.toolchain import ToolchainInfo
from adibuild.core.vivado import (
    VivadoCredentials,
    VivadoInstaller,
    VivadoInstallRequest,
)
from adibuild.utils.logger import get_logger


class DockerError(RuntimeError):
    """Raised for Docker runtime and image management errors."""


@dataclass(frozen=True)
class DockerMount:
    """A bind mount used for containerized builds."""

    source: Path
    target: Path
    read_only: bool = False


@dataclass
class DockerExecutionConfig:
    """Container execution settings for build commands."""

    image: str
    tool_version: str
    mounts: tuple[DockerMount, ...]
    workdir: Path
    home_dir: Path
    user: str | None = None
    extra_env: dict[str, str] = field(default_factory=dict)

    def build_command(
        self,
        command: str | list[str],
        env: dict[str, str] | None = None,
        cwd: Path | None = None,
    ) -> list[str]:
        """Build the docker run command for the requested build step."""
        effective_cwd = cwd or self.workdir
        docker_cmd = ["docker", "run", "--rm", "-w", str(effective_cwd)]

        if self.user:
            docker_cmd.extend(["--user", self.user])

        for mount in self.mounts:
            spec = f"{mount.source}:{mount.target}"
            if mount.read_only:
                spec += ":ro"
            docker_cmd.extend(["-v", spec])

        full_env = {"HOME": str(self.home_dir)}
        full_env.update(self.extra_env)
        if env:
            full_env.update(env)
        for key, value in sorted(full_env.items()):
            docker_cmd.extend(["-e", f"{key}={value}"])

        docker_cmd.extend([self.image, "bash", "-lc", self._build_shell_script(command)])
        return docker_cmd

    def _build_shell_script(self, command: str | list[str]) -> str:
        inner_command = command if isinstance(command, str) else shlex.join(command)
        vivado_settings = f"/opt/Xilinx/Vivado/{self.tool_version}/settings64.sh"
        vitis_settings = f"/opt/Xilinx/Vitis/{self.tool_version}/settings64.sh"
        quoted_home = shlex.quote(str(self.home_dir))

        return "\n".join(
            [
                "set -e",
                f"mkdir -p {quoted_home}",
                (
                    f"if [ -f {shlex.quote(vivado_settings)} ]; then "
                    f". {shlex.quote(vivado_settings)} >/dev/null 2>&1; "
                    f"elif [ -f {shlex.quote(vitis_settings)} ]; then "
                    f". {shlex.quote(vitis_settings)} >/dev/null 2>&1; "
                    "else "
                    f"echo 'Vivado settings script not found for {self.tool_version}' >&2; "
                    "exit 1; "
                    "fi"
                ),
                inner_command,
            ]
        )


def default_vivado_image_tag(version: str) -> str:
    """Return the default reusable image tag for a Vivado release."""
    return f"adibuild/vivado:{version}"


def container_vivado_toolchain(version: str) -> ToolchainInfo:
    """Return a synthetic Vivado toolchain descriptor for containerized builds."""
    release = VivadoInstaller().resolve_release(version)
    install_version = release.install_version
    vivado_root = Path("/opt/Xilinx/Vivado") / install_version
    vitis_root = Path("/opt/Xilinx/Vitis") / install_version
    return ToolchainInfo(
        type="vivado",
        version=release.version,
        path=vivado_root,
        env_vars={
            "XILINX_VIVADO": str(vivado_root),
            "XILINX_VITIS": str(vitis_root),
        },
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
        cross_compile_microblaze="microblazeel-xilinx-linux-gnu-",
    )


def build_docker_execution_config(
    config_data: dict[str, Any],
    *,
    image: str,
    tool_version: str,
    work_dir: Path,
    cwd: Path | None = None,
) -> DockerExecutionConfig:
    """Create a Docker execution config with mounts for source, cache, and outputs."""
    effective_cwd = (cwd or Path.cwd()).resolve()
    adibuild_root = (Path.home() / ".adibuild").resolve()
    docker_home = adibuild_root / "docker-home"
    docker_home.mkdir(parents=True, exist_ok=True)

    mount_dirs = {
        effective_cwd,
        adibuild_root,
        work_dir.resolve(),
    }

    output_dir = config_data.get("build", {}).get("output_dir")
    if output_dir:
        mount_dirs.add(_resolve_mount_path(output_dir, effective_cwd))

    for path in _iter_config_paths(config_data, effective_cwd):
        mount_dirs.add(path)

    reduced_mounts = _reduce_mounts(mount_dirs)
    uid = getattr(os, "getuid", lambda: None)()
    gid = getattr(os, "getgid", lambda: None)()
    user = f"{uid}:{gid}" if uid is not None and gid is not None else None

    return DockerExecutionConfig(
        image=image,
        tool_version=tool_version,
        mounts=tuple(
            DockerMount(source=mount, target=mount, read_only=False)
            for mount in reduced_mounts
        ),
        workdir=effective_cwd,
        home_dir=docker_home,
        user=user,
    )


class VivadoDockerImageManager:
    """Build and inspect reusable Docker images with Vivado installed."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        installer: VivadoInstaller | None = None,
    ):
        self.installer = installer or VivadoInstaller(cache_dir=cache_dir)
        self.cache_dir = self.installer.cache_dir / "images"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("adibuild.docker.image")

    def build_image(
        self,
        version: str,
        *,
        tag: str | None = None,
        credentials: VivadoCredentials | None = None,
        installer_path: Path | None = None,
        config_path: Path | None = None,
        base_image: str = "ubuntu:22.04",
    ) -> dict[str, Any]:
        """Install Vivado into a staging root and build a reusable Docker image."""
        self._ensure_docker_available()
        release = self.installer.resolve_release(version)
        tag = tag or default_vivado_image_tag(release.version)
        staging_root = self.cache_dir / release.install_version / "rootfs"
        install_root = staging_root / "opt" / "Xilinx"
        staging_root.mkdir(parents=True, exist_ok=True)
        settings_script = (
            install_root / "Vivado" / release.install_version / "settings64.sh"
        )

        if not settings_script.exists():
            self.logger.info(
                "Installing Vivado %s into Docker staging root %s",
                release.version,
                install_root,
            )
            self.installer.install(
                VivadoInstallRequest(
                    version=release.version,
                    install_dir=install_root,
                    cache_dir=self.installer.cache_dir,
                    installer_path=installer_path,
                    config_path=config_path,
                    credentials=credentials,
                )
            )
        else:
            self.logger.info("Reusing staged Vivado root at %s", install_root)

        dockerfile = staging_root / "Dockerfile"
        dockerfile.write_text(
            self._dockerfile_contents(
                base_image=base_image,
                install_version=release.install_version,
                version=release.version,
            )
        )

        build_cmd = [
            "docker",
            "build",
            "-t",
            tag,
            "-f",
            str(dockerfile),
            str(staging_root),
        ]
        self.logger.info("Building Docker image %s for Vivado %s", tag, release.version)
        subprocess.run(build_cmd, check=True)

        return {
            "tag": tag,
            "version": release.version,
            "install_version": release.install_version,
            "dockerfile": str(dockerfile),
            "staging_root": str(staging_root),
        }

    def list_images(self) -> list[dict[str, Any]]:
        """List reusable Vivado images built by adibuild."""
        self._ensure_docker_available()
        result = subprocess.run(
            [
                "docker",
                "image",
                "ls",
                "--filter",
                "label=io.adibuild.vivado.version",
                "--format",
                "{{json .}}",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        images = []
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            images.append(json.loads(line))
        return images

    def inspect_image(self, tag: str) -> dict[str, Any]:
        """Inspect a reusable image by tag."""
        self._ensure_docker_available()
        result = subprocess.run(
            ["docker", "image", "inspect", tag],
            check=True,
            capture_output=True,
            text=True,
        )
        images = json.loads(result.stdout)
        if not images:
            raise DockerError(f"Docker image not found: {tag}")
        return images[0]

    def _ensure_docker_available(self) -> None:
        try:
            subprocess.run(
                ["docker", "version"],
                check=True,
                capture_output=True,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise DockerError(
                "Docker is required for reusable Vivado image management"
            ) from exc

    @staticmethod
    def _dockerfile_contents(
        *,
        base_image: str,
        install_version: str,
        version: str,
    ) -> str:
        return f"""FROM {base_image}
LABEL io.adibuild.vivado.version="{version}"
LABEL io.adibuild.vivado.install-version="{install_version}"
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \\
    bash \\
    bc \\
    bison \\
    ca-certificates \\
    flex \\
    g++ \\
    gcc \\
    git \\
    lz4 \\
    lzop \\
    make \\
    pkg-config \\
    python3 \\
    python3-pip \\
    python3-pyelftools \\
    python3-setuptools \\
    swig \\
    uuid-dev \\
    xz-utils \\
    && rm -rf /var/lib/apt/lists/*
COPY opt/Xilinx /opt/Xilinx
ENV XILINX_VIVADO=/opt/Xilinx/Vivado/{install_version}
ENV XILINX_VITIS=/opt/Xilinx/Vitis/{install_version}
ENV PATH=/opt/Xilinx/Vivado/{install_version}/bin:/opt/Xilinx/Vitis/{install_version}/bin:$PATH
WORKDIR /workspace
CMD ["/bin/bash"]
"""


def _iter_config_paths(config_data: dict[str, Any], cwd: Path) -> set[Path]:
    paths: set[Path] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
            return
        if isinstance(value, list):
            for child in value:
                visit(child)
            return
        if not isinstance(value, str):
            return
        if value.startswith(("http://", "https://")):
            return
        if "/" not in value and "\\" not in value and not value.startswith("."):
            return

        candidate = _resolve_mount_path(value, cwd)
        paths.add(candidate)

    visit(config_data)
    return paths


def _resolve_mount_path(raw_path: str | Path, cwd: Path) -> Path:
    candidate = Path(raw_path).expanduser()
    if not candidate.is_absolute():
        candidate = (cwd / candidate).resolve()
    elif candidate.exists():
        candidate = candidate.resolve()

    if candidate.exists() and candidate.is_file():
        return candidate.parent
    return candidate


def _reduce_mounts(paths: set[Path]) -> list[Path]:
    reduced: list[Path] = []
    for path in sorted(paths, key=lambda item: (len(item.parts), str(item))):
        if any(path == existing or path.is_relative_to(existing) for existing in reduced):
            continue
        reduced.append(path)
    return reduced
