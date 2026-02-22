"""ZynqMP BOOT.BIN builder."""

import json
import os
import shutil
from pathlib import Path

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.core.executor import BuildError
from adibuild.platforms.base import Platform
from adibuild.projects.atf import ATFBuilder
from adibuild.projects.uboot import UBootBuilder


class ZynqMPBootBuilder(BuilderBase):
    """
    Builder for ZynqMP BOOT.BIN.

    Orchestrates the build of:
    - FSBL (via XSCT from XSA)
    - PMUFW (via XSCT from XSA)
    - ATF (bl31.elf)
    - U-Boot (u-boot.elf)
    - Bitstream (optional, from HDL build)

    Then uses bootgen to create the final BOOT.BIN.
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
        self.logger.info("Starting ZynqMP BOOT.BIN build flow...")

        if clean_before:
            self.clean(deep=True)

        output_dir = self.get_output_dir()
        self.make_directory(output_dir)

        # 1. Get XSA file (required for FSBL/PMUFW generation)
        xsa_path = self.config.get("boot.xsa_path")
        if not xsa_path:
            # Look in HDL build output if not specified
            hdl_out = Path(self.config.get("build.output_dir", "./build"))
            xsas = list(hdl_out.glob("**/*.xsa"))
            if xsas:
                xsa_path = str(xsas[0])
                self.logger.info(f"Auto-detected XSA from HDL build: {xsa_path}")
            else:
                raise BuildError("XSA file not found. Specify boot.xsa_path in config.")

        # 2. Build or locate FSBL and PMUFW
        fsbl_elf = self._ensure_fsbl(xsa_path)
        pmufw_elf = self._ensure_pmufw(xsa_path)

        # 3. Build or locate ATF (bl31.elf)
        atf_elf = self._ensure_atf(jobs=jobs)

        # 4. Build or locate U-Boot (u-boot.elf)
        uboot_elf = self._ensure_uboot(jobs=jobs)

        # 5. Locate Bitstream (optional)
        bit_path = self.config.get("boot.bit_path")
        if not bit_path:
            hdl_out = Path(self.config.get("build.output_dir", "./build"))
            bits = list(hdl_out.glob("**/*.bit"))
            if bits:
                bit_path = str(bits[0])
                self.logger.info(f"Auto-detected Bitstream from HDL build: {bit_path}")

        # 6. Generate BIF file
        bif_path = self._generate_bif(
            fsbl=fsbl_elf,
            pmufw=pmufw_elf,
            atf=atf_elf,
            uboot=uboot_elf,
            bitstream=bit_path
        )

        # 7. Run bootgen
        boot_bin = output_dir / "BOOT.BIN"
        self.logger.info("Running bootgen...")
        
        bootgen_cmd = [
            "bootgen", "-arch", "zynqmp", "-image", str(bif_path),
            "-w", "on", "-o", str(boot_bin)
        ]
        
        # In script mode, we might need to ensure Vivado/Vitis is sourced
        self.executor.execute(bootgen_cmd, env=self.platform.get_make_env())

        artifacts = [boot_bin, bif_path]
        if bit_path:
            artifacts.append(Path(bit_path))

        return {
            "boot_bin": str(boot_bin),
            "artifacts": [str(a) for a in artifacts],
            "output_dir": str(output_dir),
        }

    def _ensure_fsbl(self, xsa_path: str) -> Path:
        """Generate FSBL from XSA using XSCT if not provided."""
        custom_fsbl = self.config.get("boot.fsbl_path")
        if custom_fsbl:
            return Path(custom_fsbl)

        self.logger.info("Generating FSBL from XSA using XSCT...")
        fsbl_dir = self.source_dir / "fsbl"
        self.make_directory(fsbl_dir)
        
        tcl_script = fsbl_dir / "gen_fsbl.tcl"
        with open(tcl_script, "w") as f:
            f.write(f"hsi open_hw_design {xsa_path}\n")
            f.write("hsi generate_app -hw [hsi current_hw_design] -os standalone -proc psu_cortexa53_0 -app zynqmp_fsbl -compile -sw [hsi current_sw_design] -dir .\n")
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(["xsct", str(tcl_script)], cwd=fsbl_dir, env=self.platform.get_make_env())
        
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
            f.write("hsi generate_app -hw [hsi current_hw_design] -os standalone -proc psu_pmu_0 -app zynqmp_pmufw -compile -sw [hsi current_sw_design] -dir .\n")
            f.write("hsi close_hw_design [hsi current_hw_design]\n")

        self.executor.execute(["xsct", str(tcl_script)], cwd=pmufw_dir, env=self.platform.get_make_env())
        
        pmufw_elf = pmufw_dir / "executable.elf"
        if not self.script_mode and not pmufw_elf.exists():
            raise BuildError(f"PMUFW generation failed. {pmufw_elf} not found.")
        
        return pmufw_elf

    def _ensure_atf(self, jobs: int | None = None) -> Path:
        """Build ATF if bl31.elf not provided."""
        custom_atf = self.config.get("boot.atf_path")
        if custom_atf:
            return Path(custom_atf)

        self.logger.info("Building ATF...")
        atf_builder = ATFBuilder(self.config, self.platform, work_dir=self.work_dir / "atf_build", script_mode=self.script_mode)
        result = atf_builder.build(jobs=jobs)
        return Path(result["artifacts"]["bl31"])

    def _ensure_uboot(self, jobs: int | None = None) -> Path:
        """Build U-Boot if u-boot.elf not provided."""
        custom_uboot = self.config.get("boot.uboot_path")
        if custom_uboot:
            return Path(custom_uboot)

        self.logger.info("Building U-Boot...")
        uboot_builder = UBootBuilder(self.config, self.platform, work_dir=self.work_dir / "uboot_build", script_mode=self.script_mode)
        result = uboot_builder.build(jobs=jobs)
        return Path(result["artifacts"]["u-boot.elf"])

    def _generate_bif(self, fsbl: Path, pmufw: Path, atf: Path, uboot: Path, bitstream: str | None = None) -> Path:
        """Generate BIF file for bootgen."""
        bif_path = self.source_dir / "boot.bif"
        self.logger.info(f"Generating BIF file at {bif_path}...")
        
        with open(bif_path, "w") as f:
            f.write("the_ROM_image:\n")
            f.write("{\n")
            f.write(f"  [bootloader, destination_cpu=a53-0] {fsbl}\n")
            f.write(f"  [pmufw_image] {pmufw}\n")
            if bitstream:
                f.write(f"  [destination_device=pl] {bitstream}\n")
            f.write(f"  [destination_cpu=a53-0, exception_level=el-3, trustzone] {atf}\n")
            f.write(f"  [destination_cpu=a53-0, exception_level=el-2] {uboot}\n")
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
        return output_base / f"boot-{tag}-zynqmp"
