import re
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository


class HDLBuilder(BuilderBase):
    """Builder for HDL projects."""

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        """
        Initialize HDLBuilder.

        Args:
            config: Build configuration
            platform: Target platform configuration (must contain 'hdl_project' and 'carrier')
            work_dir: Working directory
            script_mode: If True, generate bash script instead of executing
        """
        super().__init__(config, platform, work_dir, script_mode=script_mode)
        self.source_dir: Path | None = None

    def prepare_source(self) -> Path:
        """
        Prepare HDL source code.

        Returns:
            Path to HDL source directory
        """
        self.logger.info("Preparing HDL source...")

        # Get repository info
        repo_url = self.config.get_repository()
        tag = self.config.get_tag()

        # Setup repository path
        # Use a separate cache for hdl repo
        repo_cache = Path.home() / ".adibuild" / "repos" / "hdl"
        self.source_dir = repo_cache

        # Initialize git repository
        self.repo = GitRepository(repo_url, repo_cache, script_builder=self.executor.script_builder)

        # Ensure repository is ready (clone/fetch/checkout)
        self.logger.info("Ensuring repository is ready...")
        self.repo.ensure_repo(ref=tag)

        if not self.script_mode and not self.source_dir.exists():
            raise BuildError(f"Failed to prepare source at {self.source_dir}")

        commit = self.repo.get_commit_sha()
        self.logger.info(f"Using commit {commit[:8]}")

        return self.source_dir

    def configure(self) -> None:
        """
        Configure the build.
        HDL builds typically don't have a separate configure step like Linux.
        Configuration is handled via make variables during build.
        """
        self.logger.info("Configuration is handled during build via make variables.")

    def build(self, clean_before: bool = False, ignore_version_check: bool = False) -> dict:
        """
        Execute HDL build.

        Args:
            clean_before: Run make clean before building
            ignore_version_check: Ignore Vivado version mismatch
        """
        # Get HDL project details from platform config
        # We expect the platform config to look like:
        # platforms:
        #   my_build:
        #     hdl_project: fmcomms2
        #     carrier: zed

        # Access the raw platform config dict if needed, or assume Platform object has what we need
        # Since Platform is generic, we might need to rely on config.get_platform() again or
        # extend Platform. But here we can just use self.platform attributes if we inject them,
        # or config.

        # Wait, Platform class in base.py takes config dict.
        # adibuild/platforms/base.py: self.config = config

        platform_config = self.platform.config
        hdl_project = platform_config.get("hdl_project")
        carrier = platform_config.get("carrier")

        if not hdl_project or not carrier:
            raise BuildError(
                "HDL build requires 'hdl_project' and 'carrier' in platform configuration"
            )

        self.logger.info(
            f"Starting HDL build for project '{hdl_project}' on carrier '{carrier}'..."
        )

        # 1. Prepare source
        self.prepare_source()

        # 2. Check toolchain
        # HDL builds require Vivado (or other tools).
        # The platform object should theoretically handle this validation?
        # LinuxBuilder calls self.platform.get_toolchain().
        # For HDL, we assume the platform implies the toolchain type (e.g. zed -> vivado).
        # We can trigger toolchain detection here.
        # But 'Platform' base class handles this.

        # Note: Vivado path must be in PATH or handled by startup script.
        # adibuild toolchain detection logic finds toolchains.
        # We might need to source settings.
        # The user guide says "source settings64.sh".
        # We can check if 'vivado' is in path.

        # Check Vivado version against requirement in source
        ignore_check_env = self._check_vivado_version(ignore_version_check)

        # Let's verify environment
        if not self.script_mode:
            # We can use 'make -v' or check specific tool
            # Ideally we check for vivado
            pass
            # BuildExecutor check_tools?

        # 3. Build Project
        project_dir = self.source_dir / "projects" / hdl_project / carrier

        if not self.script_mode and not project_dir.exists():
            raise BuildError(f"Project directory not found: {project_dir}")

        if clean_before:
            self.logger.info("Cleaning project...")
            self.clean(deep=False)

        self.logger.info(f"Building project in {project_dir}...")

        # Construct make arguments
        # Add any variables from config
        make_vars = platform_config.get("make_variables", {})
        env = None

        # Handle parallel jobs? HDL builds usually handle parallelism internally via Vivado,
        # but 'make' can also use -j. The docs say "launch synthesis for OOC IP modules in parallel".
        # ADI_MAX_OOC_JOBS system variable.

        jobs = self.config.get_parallel_jobs()
        env = {
            "ADI_MAX_OOC_JOBS": str(jobs),
        }
        if ignore_check_env == "1":
            env["ADI_IGNORE_VERSION_CHECK"] = "1"

        # Helper to format make args
        make_args = ["-C", str(project_dir)]
        for k, v in make_vars.items():
            make_args.append(f"{k}={v}")

        # Execute build
        self.executor.make(target=None, extra_args=make_args, env=env)

        # 4. Package Artifacts
        return self.package_artifacts(project_dir, hdl_project, carrier)

    def _check_vivado_version(self, ignore_check: bool) -> str:
        """
        Check if current Vivado version matches required version in source.

        Args:
            ignore_check: If True, ignore mismatch and return "1"

        Returns:
            "1" if mismatch should be ignored (set ADI_IGNORE_VERSION_CHECK=1),
            "0" if match or check skipped.

        Raises:
            BuildError: If mismatch and ignore_check is False.
        """
        if self.script_mode:
            # Cannot check file content in script mode as source isn't cloned yet
            # If user explicitly asks to ignore, we assume they want the env var set
            return "1" if ignore_check else "0"

        # Search for required version in source
        # Usually found in library/scripts/*.tcl or similar
        # Regex: set required_vivado_version "2023.2"
        # We'll search in .tcl files in library/scripts and projects/scripts
        required_version = None

        search_paths = [
            self.source_dir / "library" / "scripts",
            self.source_dir / "projects" / "scripts",
            # Fallback to root for small repos or different structures
            self.source_dir,
        ]

        # Helper to scan a file
        def scan_file(path: Path) -> str | None:
            try:
                content = path.read_text()
                # Case insensitive search for variable assignment
                # 'set required_vivado_version "2023.2"'
                # Allow spaces, quotes, optional quotes
                match = re.search(
                    r'set\s+required_vivado_version\s+"?(\d+\.\d+(?:\.\d+)?)"?',
                    content,
                    re.IGNORECASE,
                )
                if match:
                    return match.group(1)
            except Exception:
                pass
            return None

        # 1. Try specific common file locations first for speed
        common_files = [
            self.source_dir / "library" / "scripts" / "adi_ip_xilinx.tcl",
            self.source_dir / "projects" / "scripts" / "adi_project_xilinx.tcl",
        ]

        for f in common_files:
            if f.exists():
                required_version = scan_file(f)
                if required_version:
                    break

        # 2. If not found, scan directory
        if not required_version:
            for base in search_paths:
                if not base.exists():
                    continue
                # Use glob for .tcl files
                for f in base.glob("*.tcl"):
                    required_version = scan_file(f)
                    if required_version:
                        break
                if required_version:
                    break

        if not required_version:
            self.logger.warning(
                "Could not find 'required_vivado_version' in source code. Skipping version check."
            )
            return "0"

        self.logger.info(f"Project requires Vivado version: {required_version}")

        # Get current toolchain info
        try:
            toolchain = self.platform.get_toolchain()
            if toolchain.type != "vivado":
                # If using non-Vivado (unlikely for HDL), skip check
                return "0"
            current_version = toolchain.version
        except Exception:
            # If we can't detect toolchain (e.g. env var only), try manual detect
            from adibuild.core.toolchain import VivadoToolchain

            tc = VivadoToolchain().detect()
            if tc:
                current_version = tc.version
            else:
                self.logger.warning("Could not detect active Vivado version. Skipping check.")
                return "0"

        self.logger.info(f"Active Vivado version: {current_version}")

        if current_version != required_version:
            if ignore_check:
                self.logger.warning(
                    f"Vivado version mismatch ({current_version} != {required_version}). "
                    "Ignoring as requested via --ignore-version-check."
                )
                return "1"
            else:
                raise BuildError(
                    f"Vivado version mismatch! Active: {current_version}, Required: {required_version}. "
                    "Use --ignore-version-check to force build."
                )

        self.logger.info("Vivado version matches.")
        return "0"

    def clean(self, deep: bool = False) -> None:
        """
        Clean build artifacts.

        Args:
            deep: If True, perform deep clean (clean-all)
        """
        if not self.source_dir:
            self.prepare_source()

        platform_config = self.platform.config
        hdl_project = platform_config.get("hdl_project")
        carrier = platform_config.get("carrier")

        if not hdl_project or not carrier:
            self.logger.warning(
                "Cannot clean: hdl_project or carrier not defined in platform config"
            )
            return

        project_dir = self.source_dir / "projects" / hdl_project / carrier

        if not self.script_mode and not project_dir.exists():
            self.logger.warning(f"Project directory not found for cleaning: {project_dir}")
            return

        target = "clean-all" if deep else "clean"
        self.logger.info(f"Cleaning project (target: {target})...")
        self.executor.make(target, extra_args=["-C", str(project_dir)])

    def package_artifacts(self, project_dir: Path, hdl_project: str, carrier: str) -> dict:
        """Collect and package build artifacts."""
        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        # Identify artifacts
        # .xsa (Vivado 2019.2+) or .hdf (older)
        # .bit (bitstream)

        # We need to find them. They are usually in:
        # project_dir/*.sdk/system_top.xsa
        # project_dir/*.runs/impl_1/system_top.bit (or similar)

        # Let's use glob to find them
        if self.script_mode:
            # Just assume standard names for script generation
            # We can't glob in script mode properly unless we write find commands.
            # Or we assume standard ADI structure:
            # <project_name>_<carrier>.sdk/system_top.xsa
            # But the folder name might vary.
            # The docs say: "system_top.xsa file should be in the .sdk folder"
            pass

        # For now, let's look for any .xsa and .bit file in the project dir (recursively?)
        # Or look in standard locations.

        # Standard ADI hdl make flow usually puts results in `project_dir`.
        # Logs are in project_dir.
        # SDK folder is `project_dir/<name>.sdk`.

        # We'll implement a best-effort copy.

        artifacts = {"xsa": [], "bit": []}

        if not self.script_mode:
            # Find XSA
            xsas = list(project_dir.glob("**/*.xsa"))
            for xsa in xsas:
                dest = output_dir / xsa.name
                self.copy_file(xsa, dest)
                artifacts["xsa"].append(str(dest))

            # Find BIT
            bits = list(project_dir.glob("**/*.bit"))
            for bit in bits:
                dest = output_dir / bit.name
                self.copy_file(bit, dest)
                artifacts["bit"].append(str(dest))

            if not xsas and not bits:
                self.logger.warning("No artifacts (.xsa or .bit) found after build.")

        else:
            # Script mode: Generate generic copy commands
            # We can try to use find or cp with wildcards
            self.executor.execute(
                f"find {project_dir} -name '*.xsa' -exec cp {{}} {output_dir} \\;"
            )
            self.executor.execute(
                f"find {project_dir} -name '*.bit' -exec cp {{}} {output_dir} \\;"
            )

        self.logger.info(f"Artifacts packaged in {output_dir}")
        return {"artifacts": artifacts, "output_dir": str(output_dir)}

    def get_output_dir(self) -> Path:
        """Get output directory for artifacts."""
        base_out = self.config.get("build.output_dir")
        if base_out:
            return Path(base_out)

        # Default
        return self.work_dir / f"hdl-{self.config.get_tag()}-{self.platform.name}"
