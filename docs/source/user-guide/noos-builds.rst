no-OS Builds
============

This guide explains how to build `no-OS <https://github.com/analogdevicesinc/no-OS>`_ bare-metal
firmware projects using ``adibuild``.

Overview
--------

no-OS is Analog Devices' GNU Make-based bare-metal firmware framework for embedded hardware.
Projects live in ``projects/<name>/`` subdirectories of the no-OS repository. ``adibuild``
automates repository management, hardware file placement, toolchain selection, and artifact
collection.

.. mermaid::

   flowchart TD
       Start([Start Build]) --> LoadConfig[Load Config File]
       LoadConfig --> PrepSource[Clone/Prepare no-OS Source]
       PrepSource --> ValidateTC{Validate Toolchain}
       ValidateTC -->|Vivado for Xilinx| PrepHW[Copy Hardware File]
       ValidateTC -->|arm-none-eabi for STM32/etc| PrepHW
       PrepHW --> RunMake["make -C projects/<name> PLATFORM=<x>"]
       RunMake --> Collect[Collect .elf / .axf Artifacts]
       Collect --> End([Done])

       style Start fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff
       style End fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff
       style ValidateTC fill:#f9f,stroke:#333,stroke-width:2px

The build process handles:

1. Cloning the ``no-OS`` repository and checking out the specified tag.
2. Validating the toolchain (Vivado for Xilinx, ``arm-none-eabi-gcc`` for STM32/Maxim/etc.).
3. Copying the hardware file (`.xsa` or `.ioc`) into the project directory.
4. Running ``make -C projects/<noos_project> PLATFORM=<noos_platform> NO-OS=<repo_root>``.
5. Collecting ``.elf`` and ``.axf`` firmware binaries.

Supported Platforms
-------------------

.. list-table::
   :header-rows: 1
   :widths: 20 25 55

   * - Platform
     - Toolchain
     - Notes
   * - ``xilinx``
     - Vivado / Vitis
     - Requires ``.xsa`` hardware file from Vivado synthesis
   * - ``stm32``
     - ``arm-none-eabi-gcc``
     - Requires ``.ioc`` hardware file from STM32CubeMX
   * - ``linux``
     - System GCC
     - Builds a native Linux userspace application
   * - ``altera``
     - System GCC
     - Intel/Altera Quartus target
   * - ``aducm3029``
     - ``arm-none-eabi-gcc``
     - ADuCM3029 microcontroller
   * - ``maxim``
     - ``arm-none-eabi-gcc``
     - Maxim/Analog Devices embedded MCUs
   * - ``pico``
     - ``arm-none-eabi-gcc``
     - Raspberry Pi Pico / RP2040

Prerequisites
-------------

**For Xilinx (``xilinx`` platform):**

* Xilinx Vivado / Vitis installed (see :doc:`toolchain-management`)
* A ``.xsa`` hardware description file exported from Vivado after synthesis

**For STM32 / bare-metal (``stm32``, ``aducm3029``, ``maxim``, ``pico``):**

* ``arm-none-eabi-gcc`` installed:

  .. code-block:: bash

     # Ubuntu / Debian
     sudo apt install gcc-arm-none-eabi

     # macOS (Homebrew)
     brew install arm-none-eabi-gcc

* A ``.ioc`` hardware file from STM32CubeMX (STM32 only)

Configuration
-------------

Create a YAML configuration file to describe your build. The ``project`` field must be ``noos``.

Minimal Xilinx Example
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: noos
   repository: https://github.com/analogdevicesinc/no-OS.git
   tag: 2023_R2

   build:
     parallel_jobs: 8
     output_dir: ./build

   platforms:
     xilinx_ad9081:
       noos_platform: xilinx
       noos_project: ad9081_fmca_ebz
       hardware_file: /path/to/system_top.xsa
       iiod: false
       toolchain:
         preferred: vivado

STM32 Example
~~~~~~~~~~~~~

.. code-block:: yaml

   project: noos
   repository: https://github.com/analogdevicesinc/no-OS.git
   tag: 2023_R2

   platforms:
     stm32_cn0565:
       noos_platform: stm32
       noos_project: cn0565
       hardware_file: /path/to/project.ioc
       toolchain:
         preferred: bare_metal

Full Example with All Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: noos
   repository: https://github.com/analogdevicesinc/no-OS.git
   tag: 2023_R2

   build:
     parallel_jobs: 8
     output_dir: ./artifacts

   platforms:
     xilinx_ad9081_vcu118:
       noos_platform: xilinx
       noos_project: ad9081_fmca_ebz
       hardware_file: /path/to/system_top.xsa
       profile: vcu118_ad9081_m8_l4          # hardware profile variant
       iiod: true                             # enable IIO daemon
       toolchain:
         preferred: vivado
         tool_version: "2023.2"              # pin Vivado version
       make_variables:
         RELEASE: y                           # extra make variables

Configuration Reference
~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Key
     - Required
     - Description
   * - ``noos_platform``
     - **Yes**
     - Target platform: ``xilinx``, ``stm32``, ``linux``, ``altera``, ``aducm3029``, ``maxim``, ``pico``
   * - ``noos_project``
     - **Yes**
     - no-OS project name (subdirectory under ``projects/``)
   * - ``hardware_file``
     - No
     - Path to hardware file (``.xsa`` for Xilinx, ``.ioc`` for STM32)
   * - ``profile``
     - No
     - Hardware profile passed as ``PROFILE=<value>`` to make
   * - ``iiod``
     - No
     - Enable IIO daemon — passes ``IIOD=y`` or ``IIOD=n`` (default: ``false``)
   * - ``make_variables``
     - No
     - Additional make variables (dict of key: value pairs)
   * - ``toolchain.preferred``
     - No
     - Preferred toolchain type (default: derived from platform)
   * - ``toolchain.tool_version``
     - No
     - Pin Vivado version (e.g., ``"2023.2"``)

Basic Usage
-----------

Build Command
~~~~~~~~~~~~~

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081

Clean Before Build
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 --clean

Override Hardware File
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 \
     --hardware-file /new/path/to/system_top.xsa

Enable IIO Daemon
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 --iiod

Generate Build Script
~~~~~~~~~~~~~~~~~~~~~

Instead of building immediately, generate a standalone bash script:

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 --generate-script

The generated script (``~/.adibuild/work/build_noos_bare_metal.sh``) captures all
git, toolchain, make, and artifact steps so it can be run independently on any
machine with the toolchain installed.

Clean Command
~~~~~~~~~~~~~

Remove build artifacts:

.. code-block:: bash

   # Standard clean
   adibuild --config noos.yaml noos clean -p xilinx_ad9081

   # Deep clean (make reset)
   adibuild --config noos.yaml noos clean -p xilinx_ad9081 --deep

Python API
----------

You can also drive no-OS builds programmatically:

.. code-block:: python

   from adibuild.core.config import BuildConfig
   from adibuild.platforms.noos import NoOSPlatform
   from adibuild.projects.noos import NoOSBuilder

   config = BuildConfig.from_yaml("noos.yaml")
   platform_config = config.get_platform("xilinx_ad9081")
   platform_config["name"] = "xilinx_ad9081"

   platform = NoOSPlatform(platform_config)
   builder = NoOSBuilder(config, platform)

   result = builder.build(clean_before=False, jobs=8)
   print(f"Artifacts in: {result['output_dir']}")
   print(f"ELF files:    {result['artifacts']['elf']}")

Using Script Generation
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   builder = NoOSBuilder(config, platform, script_mode=True)
   builder.build()  # writes build_noos_bare_metal.sh instead of running

Output Artifacts
----------------

After a successful build, artifacts are collected in:

.. code-block:: text

   <output_dir>/noos-<project>-<tag>-<platform>/

For example, with ``output_dir: ./build``, ``noos_project: ad9081_fmca_ebz``,
``tag: 2023_R2``, ``noos_platform: xilinx``:

.. code-block:: text

   build/noos-ad9081_fmca_ebz-2023_R2-xilinx/
   ├── firmware.elf
   └── metadata.json

The ``metadata.json`` records the project name, platform, tag, and artifact paths.

.. seealso::

   - :doc:`../api-reference/projects/noos` - NoOSBuilder API reference
   - :doc:`../api-reference/platforms/noos` - NoOSPlatform API reference
   - :doc:`toolchain-management` - Toolchain detection and configuration
   - :ref:`noos-cli` - Full CLI command reference
