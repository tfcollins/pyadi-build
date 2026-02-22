BOOT.BIN Generation
===================

pyadi-build provides tools to generate a complete ``BOOT.BIN`` for Xilinx Zynq, ZynqMP, and Versal platforms. This process involves multiple components that must be built from source and then combined using Xilinx ``bootgen``.

Platform Components
-------------------

The components required for ``BOOT.BIN`` vary by platform:

Zynq-7000
~~~~~~~~~

*   **FSBL** (First Stage Boot Loader)
*   **Bitstream** (Optional)
*   **U-Boot**

ZynqMP (UltraScale+)
~~~~~~~~~~~~~~~~~~~~

*   **FSBL** (First Stage Boot Loader)
*   **PMUFW** (Platform Management Unit Firmware)
*   **Bitstream** (Optional)
*   **ATF** (ARM Trusted Firmware - ``bl31.elf``)
*   **U-Boot**

Versal
~~~~~~

*   **PLM** (Platform Loader and Manager)
*   **PSMFW** (Processor System Manager Firmware)
*   **PDI** (Programmable Device Image - replaces Bitstream)
*   **ATF** (ARM Trusted Firmware - ``bl31.elf``)
*   **U-Boot**

Builders
--------

Component Builders
~~~~~~~~~~~~~~~~~~

All boot components are built from source unless a path to a pre-built binary is provided in the configuration.

*   **ATF**: Cloned from `<https://github.com/analogdevicesinc/arm-trusted-firmware>`_ and built using ``make``.
*   **U-Boot**: Cloned from `<https://github.com/analogdevicesinc/u-boot>`_ and built using ``make``.
*   **Firmware (FSBL/PMUFW/PLM/PSMFW)**: Generated and compiled from source using Xilinx ``xsct`` and the hardware description file (``.xsa`` or ``.pdi``).

Generic Boot Builder
~~~~~~~~~~~~~~~~~~~~

The ``build-boot`` command orchestrates the entire process for any supported platform.

.. code-block:: bash

   # For Zynq
   adibuild boot build-boot -p zynq --xsa system_top.xsa

   # For ZynqMP
   adibuild boot build-boot -p zynqmp --xsa system_top.xsa

   # For Versal
   adibuild boot build-boot -p versal --pdi system_top.pdi --plm plm.elf --psmfw psmfw.elf

Required Tools
--------------

*   **Xilinx Vivado/Vitis**: Provides ``bootgen`` and ``xsct``.
*   **XSCT**: Used to generate FSBL and PMUFW from the hardware description file.
*   **Cross-compiler**: GNU toolchain appropriate for the target architecture (ARM32 for Zynq, ARM64 for ZynqMP/Versal).

Configuration
-------------

Component paths can be specified in your configuration file to skip source builds:

.. code-block:: yaml

   boot:
     xsa_path: configs/hdl/system_top.xsa
     atf_path: build/atf/bl31.elf
     uboot_path: build/uboot/u-boot.elf
     # Versal specific
     plm_path: path/to/plm.elf
     psmfw_path: path/to/psmfw.elf
     pdi_path: path/to/system_top.pdi