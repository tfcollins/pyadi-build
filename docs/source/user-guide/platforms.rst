Platform Guide
==============

This guide covers the supported hardware platforms and their specific configurations.

Supported Platforms
-------------------

pyadi-build currently supports:

- **Zynq** - Xilinx Zynq-7000 SoC (ARM Cortex-A9, 32-bit)
- **ZynqMP** - Xilinx Zynq UltraScale+ MPSoC (ARM Cortex-A53, 64-bit)

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

Platform Comparison
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Feature
     - Zynq
     - ZynqMP
   * - Architecture
     - ARM Cortex-A9 (32-bit)
     - ARM Cortex-A53 (64-bit)
   * - GCC Target
     - ``arm-linux-gnueabihf``
     - ``aarch64-linux-gnu``
   * - Kernel Image
     - ``uImage`` (~4 MB)
     - ``Image`` (~19 MB)
   * - Defconfig
     - ``zynq_xcomm_adv7511_defconfig``
     - ``adi_zynqmp_defconfig``
   * - DTB Path
     - ``arch/arm/boot/dts``
     - ``arch/arm64/boot/dts/xilinx``
   * - Build Time
     - ~10-15 min
     - ~15-20 min
   * - Common Boards
     - ZC702, ZC706, ZedBoard
     - ZCU102, ZCU106

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
