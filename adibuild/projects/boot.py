"BOOT.BIN builder for Zynq, ZynqMP and Versal."

import shutil
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.uboot import UBootBuilder


class BootBuilder(BuilderBase):
    """
    Builder for BOOT.BIN.

    Orchestrates the build of bootloader components and uses bootgen
    to create the final BOOT.BIN for Xilinx platforms.
    """

    def __init__(
        self,
        config: BuildConfig,
        platform: Platform,
        work_dir: Path | None = None,
        script_mode: bool = False,
    ):
        super().__init__(config, platform, work_dir, script_mode=script_mode)
        self.source_dir = self.work_dir / "boot"
        self.source_dir.mkdir(parents=True, exist_ok=True)

    def prepare_source(self) -> Path:
        """Prepare workspace for boot components."""
        return self.source_dir

    def configure(self) -> None:
        """Configuration handled during component builds."""
        pass

    def build(self, clean_before: bool = False, jobs: int | None = None) -> dict:
        """
        Build all components and generate BOOT.BIN.
        """
        platform_name = self.platform.__class__.__name__
        self.logger.info(f"Starting {platform_name} BOOT.BIN build flow...")

        if clean_before:
            self.clean(deep=True)

        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        # 1. Get hardware description file (XSA or PDI)
        hw_file = self.config.get("boot.xsa_path") or self.config.get("boot.pdi_path")
        if not hw_file:
            # Look in HDL build output
            hdl_out = Path(self.config.get("build.output_dir", "./build"))
            ext = ".pdi" if "Versal" in platform_name else ".xsa"
            files = list(hdl_out.glob(f"**/*{ext}"))
            if files:
                hw_file = str(files[0])
                self.logger.info(f"Auto-detected hardware file from HDL build: {hw_file}")
            elif "Versal" not in platform_name:
                raise BuildError("XSA file not found. Specify boot.xsa_path in config.")
            # Versal might not need XSA if PDI is provided separately

        # 2. Collect/Build components
        components = self._ensure_components(hw_file, jobs=jobs)

        # 3. Generate BIF file
        bif_path = self._generate_bif(components)

        # 4. Run bootgen
        boot_bin = output_dir / "BOOT.BIN"
        self.logger.info("Running bootgen...")

        arch = "zynq"
        if "ZynqMP" in platform_name:
            arch = "zynqmp"
        elif "Versal" in platform_name:
            arch = "versal"

        bootgen_cmd = [
            "bootgen",
            "-arch",
            arch,
            "-image",
            str(bif_path),
            "-w",
            "on",
            "-o",
            str(boot_bin),
        ]

        self.executor.execute(bootgen_cmd, env=self.platform.get_make_env())

        artifacts = [boot_bin, bif_path]
        for path in components.values():
            if path and isinstance(path, Path) and path.exists():
                artifacts.append(path)

        return {
            "boot_bin": str(boot_bin),
            "artifacts": [str(a) for a in artifacts],
            "output_dir": str(output_dir),
        }

    def _ensure_components(self, hw_file: str | None, jobs: int | None = None) -> dict:
        """Ensure all required boot components are present."""
        platform_name = self.platform.__class__.__name__
        components = {}

        if "ZynqPlatform" == platform_name:
            components["fsbl"] = self._ensure_fsbl(hw_file)
            components["uboot"] = self._ensure_uboot(jobs=jobs)
            components["bitstream"] = self._find_bitstream()

        elif "ZynqMPPlatform" == platform_name:
            components["fsbl"] = self._ensure_fsbl(hw_file)
            components["pmufw"] = self._ensure_pmufw(hw_file)
            components["atf"] = self._ensure_atf(jobs=jobs)
            components["uboot"] = self._ensure_uboot(
                jobs=jobs, atf_path=components["atf"]
            )
            components["bitstream"] = self._find_bitstream()

        elif "VersalPlatform" == platform_name:
            components["plm"] = self._ensure_plm(hw_file)
            components["psmfw"] = self._ensure_psmfw(hw_file)
            components["atf"] = self._ensure_atf(jobs=jobs)
            components["uboot"] = self._ensure_uboot(
                jobs=jobs, atf_path=components["atf"]
            )
            components["pdi"] = Path(hw_file) if hw_file else self._find_pdi()

        return components

    def _find_bitstream(self) -> str | None:
        """Locate bitstream file."""
        bit_path = self.config.get("boot.bit_path")
        if not bit_path:
            hdl_out = Path(self.config.get("build.output_dir", "./build"))
            bits = list(hdl_out.glob("**/*.bit"))
            if bits:
                bit_path = str(bits[0])
                self.logger.info(f"Auto-detected Bitstream from HDL build: {bit_path}")
        return bit_path

    def _find_pdi(self) -> Path | None:
        """Locate PDI file."""
        pdi_path = self.config.get("boot.pdi_path")
        if not pdi_path:
            hdl_out = Path(self.config.get("build.output_dir", "./build"))
            pdis = list(hdl_out.glob("**/*.pdi"))
            if pdis:
                pdi_path = str(pdis[0])
                self.logger.info(f"Auto-detected PDI from HDL build: {pdi_path}")
        return Path(pdi_path) if pdi_path else None

    def _ensure_fsbl(self, xsa_path: str) -> Path:
        """Generate FSBL from XSA using XSCT if not provided."""
        custom_fsbl = self.config.get("boot.fsbl_path")
        if custom_fsbl:
            return Path(custom_fsbl)

        self.logger.info("Generating FSBL from XSA using XSCT...")
        fsbl_dir = self.source_dir / "fsbl"
        self.make_directory(fsbl_dir)

        app_name = "zynqmp_fsbl" if self.platform.arch == "arm64" else "zynq_fsbl"
        proc = "psu_cortexa53_0" if self.platform.arch == "arm64" else "ps7_cortexa9_0"

        tcl_script = fsbl_dir / "gen_fsbl.tcl"
        with open(tcl_script, "w") as f:
            f.write(f"hsi open_hw_design {xsa_path}\n")
            f.write(
                f"hsi generate_app -hw [hsi current_hw_design] -os standalone -proc {proc} -app {app_name} -compile -sw [hsi current_sw_design] -dir .\n"
            )
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(
            ["xsct", str(tcl_script)], cwd=fsbl_dir, env=self.platform.get_make_env()
        )

        fsbl_elf = fsbl_dir / "executable.elf"
        if not self.script_mode and not fsbl_elf.exists():
            raise BuildError(f"FSBL generation failed. {fsbl_elf} not found.")

        return fsbl_elf

    def _ensure_pmufw(self, xsa_path: str) -> Path:
        """Generate PMUFW from XSA using XSCT if not provided."""
        custom_pmufw = self.config.get("boot.pmufw_path")
        if custom_pmufw:
            return Path(custom_pmufw)

        self.logger.info("Generating PMUFW from XSA using XSCT...")
        pmufw_dir = self.source_dir / "pmufw"
        self.make_directory(pmufw_dir)

        tcl_script = pmufw_dir / "gen_pmufw.tcl"
        with open(tcl_script, "w") as f:
            f.write(f"hsi open_hw_design {xsa_path}\n")
            f.write(
                "hsi generate_app -hw [hsi current_hw_design] -os standalone -proc psu_pmu_0 -app zynqmp_pmufw -compile -sw [hsi current_sw_design] -dir .\n"
            )
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(
            ["xsct", str(tcl_script)], cwd=pmufw_dir, env=self.platform.get_make_env()
        )

        pmufw_elf = pmufw_dir / "executable.elf"
        if not self.script_mode and not pmufw_elf.exists():
            raise BuildError(f"PMUFW generation failed. {pmufw_elf} not found.")

        return pmufw_elf

    def _ensure_plm(self, hw_file: str | None) -> Path:
        """Generate PLM from PDI/XSA using XSCT if not provided."""
        custom_plm = self.config.get("boot.plm_path")
        if custom_plm:
            return Path(custom_plm)

        if not hw_file:
            raise BuildError("Hardware file (PDI/XSA) required to generate PLM.")

        self.logger.info("Generating PLM using XSCT...")
        plm_dir = self.source_dir / "plm"
        self.make_directory(plm_dir)

        tcl_script = plm_dir / "gen_plm.tcl"
        with open(tcl_script, "w") as f:
            f.write(f"hsi open_hw_design {hw_file}\n")
            f.write(
                "hsi generate_app -hw [hsi current_hw_design] -os standalone -proc pmc_tap -app versal_plm -compile -sw [hsi current_sw_design] -dir .\n"
            )
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(
            ["xsct", str(tcl_script)], cwd=plm_dir, env=self.platform.get_make_env()
        )

        plm_elf = plm_dir / "executable.elf"
        if not self.script_mode and not plm_elf.exists():
            raise BuildError(f"PLM generation failed. {plm_elf} not found.")

        return plm_elf

    def _ensure_psmfw(self, hw_file: str | None) -> Path:
        """Generate PSMFW from PDI/XSA using XSCT if not provided."""
        custom_psmfw = self.config.get("boot.psmfw_path")
        if custom_psmfw:
            return Path(custom_psmfw)

        if not hw_file:
            raise BuildError("Hardware file (PDI/XSA) required to generate PSMFW.")

        self.logger.info("Generating PSMFW using XSCT...")
        psmfw_dir = self.source_dir / "psmfw"
        self.make_directory(psmfw_dir)

        tcl_script = psmfw_dir / "gen_psmfw.tcl"
        with open(tcl_script, "w") as f:
            f.write(f"hsi open_hw_design {hw_file}\n")
            f.write(
                "hsi generate_app -hw [hsi current_hw_design] -os standalone -proc psu_psm_0 -app versal_psmfw -compile -sw [hsi current_sw_design] -dir .\n"
            )
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(
            ["xsct", str(tcl_script)], cwd=psmfw_dir, env=self.platform.get_make_env()
        )

        psmfw_elf = psmfw_dir / "executable.elf"
        if not self.script_mode and not psmfw_elf.exists():
            raise BuildError(f"PSMFW generation failed. {psmfw_elf} not found.")

        return psmfw_elf

    def _ensure_atf(self, jobs: int | None = None) -> Path:
        """Build ATF if bl31.elf not provided."""
        custom_atf = self.config.get("boot.atf_path")
        if custom_atf:
            return Path(custom_atf)

        self.logger.info("Building ATF...")
        atf_builder = ATFBuilder(
            self.config,
            self.platform,
            work_dir=self.work_dir / "atf_build",
            script_mode=self.script_mode,
        )
        result = atf_builder.build(jobs=jobs)
        return Path(result["artifacts"]["bl31"])

    def _ensure_uboot(
        self, jobs: int | None = None, atf_path: Path | None = None
    ) -> Path:
        """Build U-Boot if u-boot.elf not provided."""
        custom_uboot = self.config.get("boot.uboot_path")
        if custom_uboot:
            return Path(custom_uboot)

        self.logger.info("Building U-Boot...")
        env_overrides = {}
        if atf_path:
            # If it's bl31.elf, try to find .bin
            bl31_bin = atf_path.with_suffix(".bin")
            if bl31_bin.exists():
                env_overrides["BL31"] = str(bl31_bin)
            else:
                env_overrides["BL31"] = str(atf_path)

        uboot_builder = UBootBuilder(
            self.config,
            self.platform,
            work_dir=self.work_dir / "uboot_build",
            script_mode=self.script_mode,
        )
        result = uboot_builder.build(jobs=jobs, env_overrides=env_overrides)

        # Zynq uses u-boot.img usually, but bootgen can use .elf
        return Path(
            result["artifacts"].get("u-boot.elf") or result["artifacts"].get("u-boot")
        )

    def _generate_bif(self, components: dict) -> Path:
        """Generate BIF file for bootgen."""
        bif_path = self.source_dir / "boot.bif"
        self.logger.info(f"Generating BIF file at {bif_path}...")

        platform_name = self.platform.__class__.__name__

        with open(bif_path, "w") as f:
            f.write("the_ROM_image:\n")
            f.write("{\n")

            if "ZynqPlatform" == platform_name:
                f.write(f"  [bootloader] {components['fsbl']}\n")
                if components.get("bitstream"):
                    f.write(f"  {components['bitstream']}\n")
                f.write(f"  {components['uboot']}\n")

            elif "ZynqMPPlatform" == platform_name:
                f.write(f"  [bootloader, destination_cpu=a53-0] {components['fsbl']}\n")
                f.write(f"  [pmufw_image] {components['pmufw']}\n")
                if components.get("bitstream"):
                    f.write(f"  [destination_device=pl] {components['bitstream']}\n")
                f.write(
                    f"  [destination_cpu=a53-0, exception_level=el-3, trustzone] {components['atf']}\n"
                )
                f.write(
                    f"  [destination_cpu=a53-0, exception_level=el-2] {components['uboot']}\n"
                )

            elif "VersalPlatform" == platform_name:
                f.write("  image {\n")
                f.write("    { type=bootloader, file=" + str(components["plm"]) + " }\n")
                f.write("    { type=pmufw, file=" + str(components["psmfw"]) + " }\n")
                if components.get("pdi"):
                    f.write("    { type=pdi, file=" + str(components["pdi"]) + " }\n")
                f.write("  }\n")
                f.write("  image {\n")
                f.write('    id = 0x1c000000, name = "atf",\n')
                f.write(
                    "    { type=el-3, trustzone, file=" + str(components["atf"]) + " }\n"
                )
                f.write("  }\n")
                f.write("  image {\n")
                f.write('    id = 0x1e000000, name = "u-boot",\n')
                f.write("    { type=el-2, file=" + str(components["uboot"]) + " }\n")
                f.write("  }\n")

            f.write("}\n")

        return bif_path

    def clean(self, deep: bool = False) -> None:
        """Clean boot components."""
        if deep:
            if self.script_mode:
                self.executor.execute(f"rm -rf {self.source_dir}")
            else:
                shutil.rmtree(self.source_dir, ignore_errors=True)
                self.source_dir.mkdir(parents=True, exist_ok=True)

    def get_output_dir(self) -> Path:
        """Get output directory for BOOT.BIN."""
        tag = self.config.get_tag() or "unknown"
        output_base = Path(self.config.get("build.output_dir", "./build"))
        return output_base / f"boot-{tag}-{self.platform.arch}"


class ZynqMPBootBuilder(BootBuilder):
    """Alias for backward compatibility."""

    pass
