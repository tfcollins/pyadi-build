ZynqMP BOOT.BIN Generation
========================

pyadi-build provides tools to generate a complete ``BOOT.BIN`` for Xilinx ZynqMP platforms. This process involves multiple components that must be built and then combined using Xilinx ``bootgen``.

Components
----------

A typical ZynqMP ``BOOT.BIN`` includes:

1.  **FSBL** (First Stage Boot Loader): Initializes hardware (DDR, etc.)
2.  **PMUFW** (Platform Management Unit Firmware): Manages power and system states
3.  **ATF** (ARM Trusted Firmware): Provides runtime services (EL3)
4.  **U-Boot**: Second stage bootloader
5.  **Bitstream**: FPGA configuration file (optional)

Builders
--------

### ARM Trusted Firmware (ATF)

Builds ``bl31.elf``.

.. code-block:: bash

   adibuild boot build-atf -p zynqmp

### U-Boot

Builds ``u-boot.elf``.

.. code-block:: bash

   adibuild boot build-uboot -p zynqmp

### ZynqMP BOOT.BIN

Orchestrates the entire process. It can auto-detect bitstreams and XSA files from previous HDL builds.

.. code-block:: bash

   adibuild boot build-zynqmp-boot -p zynqmp \
     --xsa path/to/system_top.xsa \
     --bit path/to/system_top.bit

Required Tools
--------------

- **Xilinx Vivado/Vitis**: Provides ``bootgen`` and ``xsct``.
- **XSCT**: Used to generate FSBL and PMUFW from the hardware description (XSA).
- **Cross-compiler**: Aarch64 GNU toolchain for ATF and U-Boot.

Configuration
-------------

You can specify paths to pre-built components in your configuration file:

.. code-block:: yaml

   boot:
     xsa_path: configs/hdl/system_top.xsa
     atf_path: build/atf/bl31.elf
     uboot_path: build/uboot/u-boot.elf
     fsbl_path: build/boot/fsbl/executable.elf
     pmufw_path: build/boot/pmufw/executable.elf

