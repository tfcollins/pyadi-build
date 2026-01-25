"""Linux kernel builder implementation."""

import json
import time
from datetime import datetime
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.utils.git import GitRepository


class LinuxBuilder(BuilderBase):
    """Linux kernel builder with support for multiple platforms."""

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        """
        Initialize LinuxBuilder.

        Args:
            config: Build configuration
            platform: Target platform
            work_dir: Working directory
            script_mode: If True, generate bash script instead of executing
        """
        super().__init__(config, platform, work_dir, script_mode=script_mode)

        self.source_dir: Path | None = None

        self.repo: GitRepository | None = None

        # Build state
        self._configured = False
        self._kernel_built = False
        self._dtbs_built = False

    def prepare_source(self) -> Path:
        """
        Prepare kernel source code.

        Returns:
            Path to kernel source directory
        """
        self.logger.info("Preparing Linux kernel source...")

        # Get repository info
        repo_url = self.config.get_repository()
        tag = self.config.get_tag()

        # Setup repository path
        repo_cache = Path.home() / ".adibuild" / "repos" / "linux"
        self.source_dir = repo_cache

        # Initialize git repository
        self.repo = GitRepository(repo_url, repo_cache, script_builder=self.executor.script_builder)

        # Clone/update repository and checkout tag

        self.logger.info("Ensuring repository is ready...")
        self.repo.ensure_repo(ref=tag)

        if not tag:
            self.logger.warning("No tag specified, using current HEAD")

        # Get commit info
        commit_sha = self.repo.get_commit_sha()
        self.logger.info(f"Using commit {commit_sha[:8]}")

        # Update executor working directory
        self.executor.cwd = self.source_dir

        return self.source_dir

    def configure(self, custom_config: Path | None = None, menuconfig: bool = False) -> None:
        """
        Configure the kernel.

        Args:
            custom_config: Optional path to custom .config file
            menuconfig: If True, run menuconfig after defconfig
        """
        if not self.source_dir:
            raise BuildError("Source not prepared. Call prepare_source() first.")

        self.logger.info(f"Configuring kernel with {self.platform.defconfig}...")

        # Get environment for make
        make_env = self.platform.get_make_env()

        # Load custom config or use defconfig
        if custom_config:
            self.logger.info(f"Using custom config from {custom_config}")
            self.copy_file(custom_config, self.source_dir / ".config")
            # Run olddefconfig to update
            self.executor.make("olddefconfig", env=make_env)

        else:
            # Run defconfig
            self.executor.make(self.platform.defconfig, env=make_env)

        # Run menuconfig if requested
        if menuconfig:
            self.logger.info("Running menuconfig...")
            self.executor.make("menuconfig", env=make_env)

        self._configured = True
        self.logger.info("Kernel configuration complete")

    def build_kernel(self, jobs: int | None = None) -> Path | list[Path]:
        """
        Build kernel image.

        Args:
            jobs: Number of parallel jobs

        Returns:
            Path to built kernel image (or List[Path] for MicroBlaze with multiple targets)
        """
        if not self._configured:
            raise BuildError("Kernel not configured. Call configure() first.")

        jobs = jobs or self.config.get_parallel_jobs()

        # Check if this is a MicroBlaze platform with multiple targets
        from adibuild.platforms.microblaze import MicroBlazePlatform

        if isinstance(self.platform, MicroBlazePlatform):
            return self._build_microblaze_kernel(jobs)

        self.logger.info(
            f"Building kernel target '{self.platform.kernel_target}' with {jobs} jobs..."
        )

        # Get environment
        make_env = self.platform.get_make_env()

        # Build kernel
        start_time = time.time()
        self.executor.make(self.platform.kernel_target, jobs=jobs, env=make_env)
        duration = time.time() - start_time

        self.logger.info(f"Kernel build completed in {duration:.1f}s")

        # Get kernel image path
        kernel_image = self.platform.get_kernel_image_full_path(self.source_dir)

        if not self.script_mode and not kernel_image.exists():
            raise BuildError(f"Kernel image not found at expected location: {kernel_image}")

        self._kernel_built = True
        return kernel_image

    def _build_microblaze_kernel(self, jobs: int) -> list[Path]:
        """
        Build MicroBlaze kernel with simpleImage targets.

        Args:
            jobs: Number of parallel jobs

        Returns:
            List of paths to built simpleImage targets
        """
        from adibuild.platforms.microblaze import MicroBlazePlatform

        platform = self.platform
        if not isinstance(platform, MicroBlazePlatform):
            raise BuildError("_build_microblaze_kernel called with non-MicroBlaze platform")

        # Check for rootfs.cpio.gz
        rootfs_path = self.source_dir / "rootfs.cpio.gz"
        if not rootfs_path.exists() and not self.script_mode:
            self.logger.info("rootfs.cpio.gz not found, downloading...")
            url = "https://swdownloads.analog.com/cse/microblaze/rootfs/rootfs.cpio.gz"
            try:
                self.download_file(url, rootfs_path)
                self.logger.info("Downloaded rootfs.cpio.gz")
            except Exception as e:
                raise BuildError(f"Failed to download rootfs.cpio.gz: {e}") from e
        elif self.script_mode:
            url = "https://swdownloads.analog.com/cse/microblaze/rootfs/rootfs.cpio.gz"
            self.download_file(url, rootfs_path)

        targets = platform.simpleimage_targets
        self.logger.info(f"Building {len(targets)} MicroBlaze simpleImage targets...")

        # Get environment
        make_env = platform.get_make_env()

        # Build each target
        start_time = time.time()
        built_images = []

        for target in targets:
            self.logger.info(f"Building {target}...")
            try:
                self.executor.make(target, jobs=jobs, env=make_env)

                # Find the built image
                image_path = self.source_dir / "arch" / "microblaze" / "boot" / target
                if self.script_mode or image_path.exists():
                    built_images.append(image_path)
                    self.logger.debug(f"Built simpleImage: {target}")
                else:
                    self.logger.warning(f"simpleImage not found at expected location: {image_path}")

            except BuildError as e:
                self.logger.warning(f"Failed to build target {target}: {e}")
                continue

        duration = time.time() - start_time
        self.logger.info(
            f"Built {len(built_images)}/{len(targets)} simpleImage targets in {duration:.1f}s"
        )

        if not built_images:
            raise BuildError("No simpleImage targets were successfully built")

        self._kernel_built = True
        return built_images

    def build_dtbs(
        self,
        dtbs: list[str] | None = None,
        jobs: int | None = None,
    ) -> list[Path]:
        """
        Build device tree blobs.

        Args:
            dtbs: Optional list of specific DTBs to build (uses config if None)
            jobs: Number of parallel jobs

        Returns:
            List of paths to built DTB files
        """
        from adibuild.platforms.microblaze import MicroBlazePlatform

        # Skip DTB build for MicroBlaze (DT embedded in simpleImage)
        if isinstance(self.platform, MicroBlazePlatform):
            self.logger.info("Skipping DTB build for MicroBlaze (DT embedded in simpleImage)")
            self._dtbs_built = True
            return []

        if not self._configured:
            raise BuildError("Kernel not configured. Call configure() first.")

        dtbs = dtbs or self.platform.dtbs
        if not dtbs:
            self.logger.warning("No DTBs specified, skipping DTB build")
            return []

        jobs = jobs or self.config.get_parallel_jobs()

        self.logger.info(f"Building {len(dtbs)} device tree blobs...")

        # Get environment
        make_env = self.platform.get_make_env()

        # Build DTBs individually to handle missing ones gracefully
        start_time = time.time()
        built_dtbs = []
        dtb_dir = self.source_dir / self.platform.dtb_path

        for dtb in dtbs:
            try:
                # Get correct make target (includes subdirectory if needed)
                make_target = self.platform.get_dtb_make_target(dtb)
                self.executor.make(make_target, jobs=jobs, env=make_env)
                dtb_path = dtb_dir / dtb
                if self.script_mode or dtb_path.exists():
                    built_dtbs.append(dtb_path)
                    self.logger.debug(f"Built DTB: {dtb}")
                else:
                    self.logger.warning(f"DTB build succeeded but file not found: {dtb}")

            except BuildError as e:
                self.logger.warning(f"Failed to build DTB {dtb}: {e}")
                continue

        duration = time.time() - start_time
        self.logger.info(f"Built {len(built_dtbs)}/{len(dtbs)} DTBs in {duration:.1f}s")

        if not built_dtbs:
            raise BuildError("No DTBs were successfully built")

        self._dtbs_built = True
        return built_dtbs

    def build(
        self,
        clean_before: bool = False,
        dtbs_only: bool = False,
        custom_config: Path | None = None,
    ) -> dict[str, any]:
        """
        Execute full kernel build pipeline.

        Args:
            clean_before: Clean before building
            dtbs_only: Build only DTBs (skip kernel image)
            custom_config: Optional custom configuration file

        Returns:
            Dictionary with build results
        """
        self.logger.info("Starting Linux kernel build...")
        build_start = time.time()

        # Validate environment
        self.validate_environment()

        # Prepare source
        if not self.source_dir:
            self.prepare_source()

        # Clean if requested
        if clean_before:
            self.clean()

        # Configure
        self.configure(custom_config=custom_config)

        # Build kernel
        kernel_image = None
        if not dtbs_only:
            kernel_image = self.build_kernel()

        # Build DTBs
        dtbs = self.build_dtbs()

        # Package artifacts
        artifacts = self.package_artifacts(kernel_image, dtbs)

        build_duration = time.time() - build_start

        self.logger.info(f"Build completed successfully in {build_duration:.1f}s")

        return {
            "success": True,
            "duration": build_duration,
            "kernel_image": kernel_image,
            "dtbs": dtbs,
            "artifacts": artifacts,
        }

    def package_artifacts(
        self,
        kernel_image: Path | list[Path] | None,
        dtbs: list[Path],
    ) -> Path:
        """
        Package build artifacts to output directory.

        Args:
            kernel_image: Path to kernel image (or List[Path] for MicroBlaze)
            dtbs: List of DTB paths

        Returns:
            Path to output directory
        """
        self.logger.info("Packaging build artifacts...")

        # Get output directory
        output_dir = self.get_output_dir()

        # Copy kernel image(s)
        if kernel_image:
            # Handle both single image and list of images (MicroBlaze)
            if isinstance(kernel_image, list):
                for img in kernel_image:
                    output_kernel = output_dir / img.name
                    self.copy_file(img, output_kernel)
                self.logger.info(f"Copied {len(kernel_image)} kernel images to {output_dir}")
            else:
                output_kernel = output_dir / kernel_image.name
                self.copy_file(kernel_image, output_kernel)
                self.logger.info(f"Copied kernel image to {output_kernel}")

        # Copy DTBs
        if dtbs:
            dtb_output_dir = output_dir / "dts"
            self.make_directory(dtb_output_dir)

            for dtb in dtbs:
                output_dtb = dtb_output_dir / dtb.name
                self.copy_file(dtb, output_dtb)

            self.logger.info(f"Copied {len(dtbs)} DTBs to {dtb_output_dir}")

        # Generate metadata (skip in script mode for now or implement file writing via echo)
        if not self.script_mode:
            if isinstance(kernel_image, list):
                kernel_images = [img.name for img in kernel_image]
            elif kernel_image:
                kernel_images = [kernel_image.name]
            else:
                kernel_images = []

            metadata = {
                "project": self.config.get_project(),
                "platform": self.platform.arch,
                "defconfig": self.platform.defconfig,
                "tag": self.config.get_tag(),
                "commit_sha": self.repo.get_commit_sha() if self.repo else None,
                "build_date": datetime.now().isoformat(),
                "toolchain": {
                    "type": self.toolchain.type,
                    "version": self.toolchain.version,
                },
                "artifacts": {
                    "kernel_images": kernel_images,
                    "dtbs": [dtb.name for dtb in dtbs],
                },
            }

            metadata_file = output_dir / "metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            self.logger.info(f"Generated metadata: {metadata_file}")

        self.logger.info(f"All artifacts packaged in: {output_dir}")

        return output_dir

    def clean(self, deep: bool = False) -> None:
        """
        Clean build artifacts.

        Args:
            deep: If True, run mrproper (full clean)
        """
        if not self.source_dir:
            self.logger.warning("Source directory not set, nothing to clean")
            return

        target = "mrproper" if deep else "clean"
        self.logger.info(f"Running make {target}...")

        # Get environment
        make_env = self.platform.get_make_env()

        # Update executor working directory
        self.executor.cwd = self.source_dir

        # Run clean
        self.executor.make(target, env=make_env)

        # Reset build state
        self._configured = False
        self._kernel_built = False
        self._dtbs_built = False

        self.logger.info("Clean completed")

    def menuconfig(self) -> None:
        """
        Run menuconfig for interactive kernel configuration.

        Requires kernel to be configured first.
        """
        if not self.source_dir:
            raise BuildError("Source not prepared. Call prepare_source() first.")

        self.logger.info("Running menuconfig...")

        # Get environment
        make_env = self.platform.get_make_env()

        # Update executor working directory
        self.executor.cwd = self.source_dir

        # Run menuconfig
        self.executor.make("menuconfig", env=make_env)

        self.logger.info("Menuconfig completed")
