Platform Guide
==============

This guide covers the supported hardware platforms and their specific configurations.

Supported Platforms
-------------------

pyadi-build currently supports:

- **Zynq** - Xilinx Zynq-7000 SoC (ARM Cortex-A9, 32-bit)
- **ZynqMP** - Xilinx Zynq UltraScale+ MPSoC (ARM Cortex-A53, 64-bit)
- **MicroBlaze** - Xilinx Virtex FPGAs (MicroBlaze soft-core processor)

Zynq Platform
-------------

Overview
~~~~~~~~

The Zynq platform targets Xilinx Zynq-7000 SoC devices:

- **Architecture**: ARM Cortex-A9 (32-bit)
- **GCC Target**: ``arm-linux-gnueabihf``
- **Kernel Image**: ``uImage`` (U-Boot wrapped)
- **Defconfig**: ``zynq_xcomm_adv7511_defconfig``

Supported Boards
~~~~~~~~~~~~~~~~

- **ZC702** - Zynq-7000 evaluation board
- **ZC706** - Zynq-7000 evaluation board
- **ZedBoard** - Community Zynq-7000 board
- Custom Zynq boards with ADI FMC cards

ADI FMC Cards Supported
~~~~~~~~~~~~~~~~~~~~~~~

- **FMCOMMS2/3** - AD9361 RF transceiver
- **FMCOMMS4** - AD9364 RF transceiver
- **FMCOMMS5** - Dual AD9361
- **AD-FMCDAQ2-EBZ** - High-speed data acquisition

Configuration
~~~~~~~~~~~~~

**Default Configuration (``configs/linux/zynq.yaml``):**

.. code-block:: yaml

   platforms:
     zynq:
       arch: arm
       cross_compile: arm-linux-gnueabihf-
       defconfig: zynq_xcomm_adv7511_defconfig
       kernel_target: uImage
       dtb_path: arch/arm/boot/dts
       kernel_image_path: arch/arm/boot/uImage

       dtbs:
         - zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
         - zynq-zc702-adv7511-ad9364-fmcomms4.dtb
         - zynq-zc706-adv7511-ad9361-fmcomms2-3.dtb
         - zynq-zc706-adv7511-ad9364-fmcomms4.dtb
         - zynq-zc706-adv7511-ad9361-fmcomms5.dtb

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

Building for Zynq
~~~~~~~~~~~~~~~~~

**CLI:**

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2

**Python API:**

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqPlatform

   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
   platform_config = config.get_platform('zynq')
   platform = ZynqPlatform(platform_config)

   builder = LinuxBuilder(config, platform)
   result = builder.build()

Build Outputs
~~~~~~~~~~~~~

.. code-block:: text

   build/linux-2023_R2-arm/
   ├── uImage                   # U-Boot wrapped kernel (~4 MB)
   ├── dts/
   │   ├── zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
   │   ├── zynq-zc702-adv7511-ad9364-fmcomms4.dtb
   │   └── ...
   └── metadata.json

Device Tree Blobs
~~~~~~~~~~~~~~~~~

Common Zynq DTBs:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - DTB File
     - Board + FMC
   * - ``zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb``
     - ZC702 + FMCOMMS2/3
   * - ``zynq-zc702-adv7511-ad9364-fmcomms4.dtb``
     - ZC702 + FMCOMMS4
   * - ``zynq-zc706-adv7511-ad9361-fmcomms2-3.dtb``
     - ZC706 + FMCOMMS2/3
   * - ``zynq-zc706-adv7511-ad9361-fmcomms5.dtb``
     - ZC706 + FMCOMMS5
   * - ``zynq-zed-adv7511-ad9361-fmcomms2-3.dtb``
     - ZedBoard + FMCOMMS2/3

ZynqMP Platform
---------------

Overview
~~~~~~~~

The ZynqMP platform targets Xilinx Zynq UltraScale+ MPSoC devices:

- **Architecture**: ARM Cortex-A53 (64-bit)
- **GCC Target**: ``aarch64-linux-gnu``
- **Kernel Image**: ``Image`` (raw ARM64 binary)
- **Defconfig**: ``adi_zynqmp_defconfig``

Supported Boards
~~~~~~~~~~~~~~~~

- **ZCU102** - Zynq UltraScale+ evaluation board
- **ZCU106** - Zynq UltraScale+ evaluation board
- Custom ZynqMP boards with ADI FMC cards

ADI FMC Cards Supported
~~~~~~~~~~~~~~~~~~~~~~~

- **FMCOMMS2/3** - AD9361 RF transceiver
- **FMCOMMS4** - AD9364 RF transceiver
- **FMCOMMS8** - ADRV9009 wideband transceiver
- **AD-FMCDAQ2-EBZ** - High-speed data acquisition
- **AD-FMCDAQ3-EBZ** - High-speed data acquisition

Configuration
~~~~~~~~~~~~~

**Default Configuration (``configs/linux/zynqmp.yaml``):**

.. code-block:: yaml

   platforms:
     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtb_path: arch/arm64/boot/dts/xilinx
       kernel_image_path: arch/arm64/boot/Image

       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
         - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
         - zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb
         - zynqmp-zcu102-rev10-ad9371-fmcomms8.dtb
         - zynqmp-zcu102-rev10-ad9081-fmcomms8.dtb
         - zynqmp-zcu102-rev10-ad9082-fmcomms8.dtb

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

Building for ZynqMP
~~~~~~~~~~~~~~~~~~~

**CLI:**

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

**Python API:**

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqMPPlatform

   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)

   builder = LinuxBuilder(config, platform)
   result = builder.build()

Build Outputs
~~~~~~~~~~~~~

.. code-block:: text

   build/linux-2023_R2-arm64/
   ├── Image                    # Raw ARM64 kernel (~19 MB)
   ├── dts/
   │   ├── zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   │   ├── zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
   │   ├── zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb
   │   └── ...
   └── metadata.json

Device Tree Blobs
~~~~~~~~~~~~~~~~~

Common ZynqMP DTBs:

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - DTB File
     - Board + FMC
   * - ``zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb``
     - ZCU102 + FMCOMMS2/3
   * - ``zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb``
     - ZCU102 + FMCOMMS4
   * - ``zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb``
     - ZCU102 + FMCOMMS8 (ADRV9009)
   * - ``zynqmp-zcu102-rev10-ad9371-fmcomms8.dtb``
     - ZCU102 + FMCOMMS8 (AD9371)
   * - ``zynqmp-zcu102-rev10-ad9081-fmcomms8.dtb``
     - ZCU102 + FMCOMMS8 (AD9081)
   * - ``zynqmp-zcu102-rev10-ad9082-fmcomms8.dtb``
     - ZCU102 + FMCOMMS8 (AD9082)

MicroBlaze Platform
-------------------

Overview
~~~~~~~~

The MicroBlaze platform targets Xilinx Virtex FPGAs with MicroBlaze soft-core processors:

- **Architecture**: MicroBlaze soft-core (32-bit)
- **GCC Target**: ``microblazeel-xilinx-linux-gnu``
- **Kernel Image**: ``simpleImage.<dts>`` (device tree embedded)
- **Defconfig**: ``adi_mb_defconfig``

Supported Boards
~~~~~~~~~~~~~~~~

- **VCU118** - Virtex UltraScale+ FPGA development board
- **KC705** - Kintex-7 FPGA development board
- **KCU105** - Kintex UltraScale FPGA development board
- **VC707** - Virtex-7 FPGA development board
- **VCU128** - Virtex UltraScale+ HBM FPGA platform
- Custom Virtex boards with ADI FMC cards

ADI FMC Cards Supported
~~~~~~~~~~~~~~~~~~~~~~~

- **AD9081-FMCA-EBZ** - MxFE™ mixed-signal front end
- **AD9082** - MxFE™ mixed-signal front end
- **ADRV9009** - Wideband RF transceiver
- **FMCOMMS8** - ADRV9009/AD9371 FMC module

Configuration
~~~~~~~~~~~~~

**Default Configuration (``configs/linux/microblaze.yaml``):**

.. code-block:: yaml

   platforms:
     microblaze:
       arch: microblaze
       cross_compile: microblazeel-xilinx-linux-gnu-
       defconfig: adi_mb_defconfig
       kernel_target: simpleImage.system
       dtb_path: arch/microblaze/boot/dts
       kernel_image_path: arch/microblaze/boot/simpleImage.system

       simpleimage_targets:
         - simpleImage.system

       dtbs: []

       toolchain:
         preferred: vivado
         fallback: []

**VCU118 + AD9081 Configuration (``configs/linux/microblaze_vcu118_ad9081.yaml``):**

.. code-block:: yaml

   platforms:
     microblaze_vcu118:
       arch: microblaze
       cross_compile: microblazeel-xilinx-linux-gnu-
       defconfig: adi_mb_defconfig
       kernel_target: simpleImage.vcu118_ad9081

       simpleimage_targets:
         - simpleImage.vcu118_ad9081

       board: VCU118
       fmc: AD9081

Building for MicroBlaze
~~~~~~~~~~~~~~~~~~~~~~~

**CLI:**

.. code-block:: bash

   # Build with default configuration
   adibuild linux build -p microblaze -t 2023_R2

   # Build for VCU118 + AD9081
   adibuild linux build -p microblaze_vcu118 \
     --config configs/linux/microblaze_vcu118_ad9081.yaml \
     -t 2023_R2

**Python API:**

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import MicroBlazePlatform

   config = BuildConfig.from_yaml('configs/linux/microblaze_vcu118_ad9081.yaml')
   platform_config = config.get_platform('microblaze_vcu118')
   platform = MicroBlazePlatform(platform_config)

   builder = LinuxBuilder(config, platform)
   result = builder.build()

Build Outputs
~~~~~~~~~~~~~

.. code-block:: text

   build/microblaze_vcu118_ad9081/
   ├── simpleImage.vcu118_ad9081    # Kernel with embedded DT (~4 MB)
   └── metadata.json                 # Build metadata

**Note:** Unlike Zynq/ZynqMP, MicroBlaze does not produce separate DTB files.
The device tree is embedded directly in the ``simpleImage`` file.

simpleImage Format
~~~~~~~~~~~~~~~~~~

MicroBlaze uses the ``simpleImage`` kernel format which includes:

- Compressed kernel binary
- Embedded device tree blob (DT)
- Bootstrap code

This self-contained format allows the kernel to boot without requiring separate DTB files.

Multiple simpleImage Targets
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

MicroBlaze platforms can build multiple simpleImage targets with different device trees:

.. code-block:: yaml

   platforms:
     microblaze_custom:
       simpleimage_targets:
         - simpleImage.vcu118_ad9081
         - simpleImage.vcu118_ad9082
         - simpleImage.vcu118_adrv9009

Each target produces a separate kernel image with its corresponding device tree.

Platform-Specific Features for MicroBlaze
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Vivado Toolchain Required:**

MicroBlaze requires Xilinx Vivado or Vitis for the cross-compiler:

.. code-block:: bash

   # Source Vivado environment
   source /opt/Xilinx/Vivado/2023.2/settings64.sh

   # Verify toolchain
   which microblazeel-xilinx-linux-gnu-gcc

**No Fallback Toolchains:**

Unlike Zynq/ZynqMP, MicroBlaze has no ARM GNU or system toolchain fallback.
Vivado/Vitis installation is mandatory.

**ADI Reference Designs:**

MicroBlaze support is designed for ADI reference designs available at:
https://analogdevicesinc.github.io/documentation/linux/kernel/microblaze.html

Platform Comparison
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 27 27 26

   * - Feature
     - Zynq
     - ZynqMP
     - MicroBlaze
   * - Architecture
     - ARM Cortex-A9 (32-bit)
     - ARM Cortex-A53 (64-bit)
     - MicroBlaze soft-core (32-bit)
   * - GCC Target
     - ``arm-linux-gnueabihf``
     - ``aarch64-linux-gnu``
     - ``microblazeel-xilinx-linux-gnu``
   * - Kernel Image
     - ``uImage`` (~4 MB)
     - ``Image`` (~19 MB)
     - ``simpleImage.<dts>`` (~4 MB)
   * - Defconfig
     - ``zynq_xcomm_adv7511_defconfig``
     - ``adi_zynqmp_defconfig``
     - ``adi_mb_defconfig``
   * - DTB Path
     - ``arch/arm/boot/dts``
     - ``arch/arm64/boot/dts/xilinx``
     - ``arch/microblaze/boot/dts``
   * - Separate DTBs
     - Yes
     - Yes
     - No (embedded)
   * - Build Time
     - ~10-15 min
     - ~15-20 min
     - ~12-18 min
   * - Common Boards
     - ZC702, ZC706, ZedBoard
     - ZCU102, ZCU106
     - VCU118, KC705, KCU105
   * - Toolchain
     - Vivado/ARM GNU/System
     - Vivado/ARM GNU/System
     - Vivado only

Platform-Specific Features
---------------------------

Zynq-Specific
~~~~~~~~~~~~~

**U-Boot Image Wrapping:**

Zynq uses ``uImage`` which includes a U-Boot header:

.. code-block:: text

   uImage = U-Boot header + compressed zImage

This allows U-Boot to boot the kernel directly.

**LOADADDR:**

The kernel load address is embedded in the uImage header (typically ``0x8000``).

ZynqMP-Specific
~~~~~~~~~~~~~~~

**Raw Image:**

ZynqMP uses raw ``Image`` format without U-Boot wrapper. U-Boot loads it directly.

**EFI Stub:**

The kernel includes EFI stub support for UEFI booting.

**64-bit Address Space:**

ZynqMP can address more than 4 GB of RAM, enabling larger kernels and buffers.

MicroBlaze-Specific
~~~~~~~~~~~~~~~~~~~

**simpleImage Format:**

MicroBlaze uses ``simpleImage`` format which embeds the device tree directly in the kernel:

.. code-block:: text

   simpleImage = kernel + DT + bootstrap

Unlike Zynq/ZynqMP which produce separate DTB files, the device tree is compiled into the kernel image.

**No Separate DTBs:**

The ``dtbs`` configuration list should be empty for MicroBlaze platforms.
Device trees are specified via device tree source names in ``simpleimage_targets``.

**Multiple Targets:**

A single MicroBlaze configuration can build multiple kernel images with different device trees
using the ``simpleimage_targets`` property.

**Vivado Mandatory:**

MicroBlaze cross-compiler is only available through Xilinx Vivado/Vitis.
There is no ARM GNU or system toolchain fallback like Zynq/ZynqMP.

Custom Platform Configuration
------------------------------

Creating a Custom Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For custom boards, create a new configuration:

.. code-block:: yaml

   platforms:
     my_zynqmp_board:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig  # Or custom defconfig
       kernel_target: Image
       dtb_path: arch/arm64/boot/dts/xilinx
       kernel_image_path: arch/arm64/boot/Image

       dtbs:
         - my-custom-board.dtb

       toolchain:
         preferred: vivado
         fallback:
           - arm

Build with custom platform:

.. code-block:: bash

   adibuild --config my_config.yaml linux build -p my_zynqmp_board

Custom Defconfig
~~~~~~~~~~~~~~~~

To use a custom defconfig:

1. **Create defconfig:**

   .. code-block:: bash

      # Start with default
      cp configs/linux/zynqmp.yaml my_config.yaml

      # Edit to use custom defconfig
      nano my_config.yaml

   .. code-block:: yaml

      platforms:
        zynqmp:
          defconfig: my_custom_zynqmp_defconfig

2. **Place defconfig in kernel source:**

   .. code-block:: bash

      cp my_custom_zynqmp_defconfig ~/.adibuild/work/linux/arch/arm64/configs/

3. **Build:**

   .. code-block:: bash

      adibuild --config my_config.yaml linux build -p zynqmp

Platform Detection
------------------

Python API
~~~~~~~~~~

Detect platform from configuration:

.. code-block:: python

   from adibuild import BuildConfig

   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # List available platforms
   platforms = config.get('platforms', {}).keys()
   print(f"Available platforms: {list(platforms)}")

   # Get platform details
   for name in platforms:
       platform_config = config.get_platform(name)
       print(f"{name}: {platform_config['arch']}")

Best Practices
--------------

1. **Use default configurations** as starting points

2. **Build for target platform** - don't cross-use Zynq/ZynqMP configs

3. **Select appropriate DTBs** - only build DTBs for your hardware

4. **Test on hardware** - verify DTBs work on actual boards

5. **Version control custom configs** - track platform-specific changes

6. **Document custom platforms** - explain differences from defaults

Next Steps
----------

- Learn about :doc:`build-outputs` for artifact details
- See :doc:`../examples/index` for platform-specific examples
- Check :doc:`configuration-guide` for complete platform configuration reference
