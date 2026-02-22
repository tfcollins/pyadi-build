BOOT.BIN Generation
===================

pyadi-build provides tools to generate a complete ``BOOT.BIN`` for Xilinx Zynq, ZynqMP, and Versal platforms. This process involves multiple components that must be built and then combined using Xilinx ``bootgen``.

Platform Components
-------------------

The components required for ``BOOT.BIN`` vary by platform:

Zynq (7000 series)
~~~~~~~~~~~~~~~~~~
1.  **FSBL** (First Stage Boot Loader)
2.  **Bitstream** (Optional)
3.  **U-Boot**

ZynqMP (UltraScale+)
~~~~~~~~~~~~~~~~~~~~
1.  **FSBL** (First Stage Boot Loader)
2.  **PMUFW** (Platform Management Unit Firmware)
3.  **Bitstream** (Optional)
4.  **ATF** (ARM Trusted Firmware - ``bl31.elf``)
5.  **U-Boot**

Versal
~~~~~~
1.  **PLM** (Platform Loader and Manager)
2.  **PSMFW** (Processor System Manager Firmware)
3.  **PDI** (Programmable Device Image - replaces Bitstream)
4.  **ATF** (ARM Trusted Firmware)
5.  **U-Boot**

Builders
--------

### Generic Boot Builder

The ``build-boot`` command orchestrates the entire process for any supported platform.

.. code-block:: bash

   # For Zynq
   adibuild boot build-boot -p zynq --xsa system_top.xsa

   # For ZynqMP
   adibuild boot build-boot -p zynqmp --xsa system_top.xsa

   # For Versal
   adibuild boot build-boot -p versal --pdi system_top.pdi --plm plm.elf --psmfw psmfw.elf

### Component Builders

You can also build individual components:

.. code-block:: bash

   # Build ATF for ZynqMP/Versal
   adibuild boot build-atf -p zynqmp

   # Build U-Boot
   adibuild boot build-uboot -p zynqmp

Required Tools
--------------

- **Xilinx Vivado/Vitis**: Provides ``bootgen`` and ``xsct``.
- **XSCT**: Used to generate FSBL and PMUFW from the hardware description (XSA).
- **Cross-compiler**: GNU toolchain appropriate for the target architecture (ARM32 for Zynq, ARM64 for ZynqMP/Versal).

Configuration
-------------

Component paths can be specified in your configuration file:

.. code-block:: yaml

   boot:
     xsa_path: configs/hdl/system_top.xsa
     atf_path: build/atf/bl31.elf
     uboot_path: build/uboot/u-boot.elf
     # Versal specific
     plm_path: path/to/plm.elf
     psmfw_path: path/to/psmfw.elf
     pdi_path: path/to/system_top.pdi