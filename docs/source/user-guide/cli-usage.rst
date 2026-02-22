CLI Usage
=========

This guide provides a complete reference for the pyadi-build command-line interface.

Overview
--------

The ``adibuild`` CLI is organized into command groups for managing configurations, toolchains, and project builds.

.. mermaid::

   graph LR
       CLI[adibuild] --> Config[config]
       CLI --> Linux[linux]
       CLI --> HDL[hdl]
       CLI --> NoOS[noos]
       CLI --> LibAD9361[libad9361]
       CLI --> Genalyzer[genalyzer]
       CLI --> Toolchain[toolchain]

       Config --> Init[init]
       Config --> Validate[validate]

       Linux --> LBuild[build]
       Linux --> LMenu[menuconfig]
       Linux --> LDtbs[dtbs]

       HDL --> HBuild[build]

       NoOS --> NBuild[build]
       NoOS --> NClean[clean]

       LibAD9361 --> LibBuild[build]
       LibAD9361 --> LibClean[clean]

       Genalyzer --> GBuild[build]
       Genalyzer --> GClean[clean]

       style CLI fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff

The ``adibuild`` CLI is organized into command groups:

- **linux** - Linux kernel build commands
- **hdl** - HDL project build commands
- **noos** - no-OS bare-metal firmware build commands
- **libad9361** - libad9361-iio library build commands
- **genalyzer** - Genalyzer DSP analysis library build commands
- **config** - Configuration management
- **toolchain** - Toolchain detection and information

Global Options
--------------

These options apply to all commands:

.. code-block:: bash

   adibuild [OPTIONS] COMMAND [ARGS]...

Options:

.. option:: --version

   Show version and exit

.. option:: --verbose, -v

   Increase verbosity (can be used multiple times: ``-v``, ``-vv``)

   - No flag: Warnings only
   - ``-v``: Info messages
   - ``-vv``: Debug messages

.. option:: --config PATH, -c PATH

   Path to custom configuration file

Examples:

.. code-block:: bash

   # Show version
   adibuild --version

   # Enable verbose output
   adibuild -v linux build -p zynqmp -t 2023_R2

   # Use custom config
   adibuild --config my_config.yaml linux build -p zynqmp

HDL Project Commands
--------------------

Build Command
~~~~~~~~~~~~~

Build an HDL project for the specified platform.

.. code-block:: bash

   adibuild hdl build [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   Target platform defined in config (e.g., ``zed_fmcomms2``). Mutually exclusive with ``--project``/``--carrier``.

.. option:: --project PROJECT

   HDL project name (e.g., ``fmcomms2``). Required if platform not used.

.. option:: --carrier CARRIER

   Carrier board name (e.g., ``zed``). Required if platform not used.

.. option:: --arch ARCH

   Target architecture (default: ``unknown``). Used for output directory naming.

.. option:: --tag TAG, -t TAG

   Git tag or branch to build.

.. option:: --output DIR, -o DIR

   Output directory for build artifacts.

.. option:: --clean

   Clean before building (runs ``make clean``).

.. option:: --jobs N, -j N

   Number of parallel jobs (sets ``ADI_MAX_OOC_JOBS``).

.. option:: --ignore-version-check

   Force build even if Vivado version does not match requirement.

.. option:: --generate-script

   Generate a bash script instead of executing the build.

**Examples:**

Using config file:

.. code-block:: bash

   adibuild hdl build -p zed_fmcomms2

Using dynamic arguments:

.. code-block:: bash

   adibuild hdl build --project fmcomms2 --carrier zed

Force build with version mismatch:

.. code-block:: bash

   adibuild hdl build -p zed_fmcomms2 --ignore-version-check

.. _noos-cli:

no-OS Commands
--------------

Build Command
~~~~~~~~~~~~~

Build a no-OS bare-metal firmware project.

.. code-block:: bash

   adibuild noos build [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config (e.g., ``xilinx_ad9081``).

.. option:: --tag TAG, -t TAG

   Git tag or branch to build (e.g., ``2023_R2``).

.. option:: --hardware-file PATH

   Path to hardware file (``.xsa`` for Xilinx, ``.ioc`` for STM32).
   Overrides the ``hardware_file`` key in the config.

.. option:: --profile PROFILE

   Hardware profile variant. Passed as ``PROFILE=<value>`` to make.

.. option:: --iiod

   Enable IIO daemon (passes ``IIOD=y`` to make). Overrides config.

.. option:: --clean

   Run ``make clean`` before building.

.. option:: --jobs N, -j N

   Number of parallel make jobs.

.. option:: --generate-script

   Generate a bash build script instead of executing the build.
   Written to ``~/.adibuild/work/build_noos_bare_metal.sh``.

.. option:: --tool-version VERSION, -tv VERSION

   Override Vivado version (e.g., ``2023.2``). Auto-detected from
   the release tag if not specified.

**Examples:**

Build with a config file:

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081

Override hardware file:

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 \
     --hardware-file /path/to/system_top.xsa

Enable IIO daemon and clean first:

.. code-block:: bash

   adibuild --config noos.yaml noos build -p xilinx_ad9081 --iiod --clean

Generate a portable build script:

.. code-block:: bash

   adibuild --config noos.yaml noos build -p stm32_ad9081 --generate-script

Clean Command
~~~~~~~~~~~~~

Remove no-OS build artifacts.

.. code-block:: bash

   adibuild noos clean [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config.

.. option:: --tag TAG, -t TAG

   Git tag or branch (to locate the correct repository checkout).

.. option:: --deep

   Use ``make reset`` instead of ``make clean`` for a full clean.

**Examples:**

Standard clean:

.. code-block:: bash

   adibuild --config noos.yaml noos clean -p xilinx_ad9081

Deep clean:

.. code-block:: bash

   adibuild --config noos.yaml noos clean -p xilinx_ad9081 --deep

Linux Kernel Commands
---------------------

Build Command
~~~~~~~~~~~~~

Build a Linux kernel for the specified platform.

.. code-block:: bash

   adibuild linux build [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Target platform. Choices: ``zynq``, ``zynqmp``

.. option:: --tag TAG, -t TAG

   Git tag or branch to build (e.g., ``2023_R2``, ``main``)

.. option:: --defconfig DEFCONFIG

   Override default defconfig

.. option:: --output DIR, -o DIR

   Output directory for build artifacts

.. option:: --clean

   Clean before building (runs ``make clean``)

.. option:: --dtbs-only

   Build only device tree blobs, not the kernel


.. option:: --jobs N, -j N

   Number of parallel jobs (default: number of CPU cores)

.. option:: --generate-script

   Generate a bash script (e.g., ``build_linux_arm64.sh``) instead of executing the build. Useful for dry runs, debugging, or creating portable build scripts.

**Examples:**

Basic build:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

Build with clean:

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2 --clean

Build only device trees:

.. code-block:: bash

   adibuild linux build -p zynqmp --dtbs-only

Use 16 parallel jobs:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 -j 16

Custom output directory:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 -o /tmp/build


Override defconfig:

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2 --defconfig defconfig

Generate build script (dry run):

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 --generate-script

Configure Command
~~~~~~~~~~~~~~~~~

Configure kernel without building.

.. code-block:: bash

   adibuild linux configure [OPTIONS]

This runs the defconfig step and prepares the kernel for building.

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Target platform

.. option:: --tag TAG, -t TAG

   Git tag or branch

.. option:: --defconfig DEFCONFIG

   Override default defconfig

**Example:**

.. code-block:: bash

   adibuild linux configure -p zynqmp -t 2023_R2

Menuconfig Command
~~~~~~~~~~~~~~~~~~

Run interactive kernel configuration (menuconfig).

.. code-block:: bash

   adibuild linux menuconfig [OPTIONS]

Requires ncurses libraries to be installed.

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Target platform

.. option:: --tag TAG, -t TAG

   Git tag or branch

**Examples:**

.. code-block:: bash

   adibuild linux menuconfig -p zynqmp -t 2023_R2

After making changes in menuconfig, build with the customized configuration:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

DTBs Command
~~~~~~~~~~~~

Build specific device tree blobs.

.. code-block:: bash

   adibuild linux dtbs [OPTIONS] [DTB_FILES]...

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Target platform

.. option:: --tag TAG, -t TAG

   Git tag or branch

Arguments:

.. option:: DTB_FILES

   One or more DTB files to build. If not specified, builds all DTBs from config.

**Examples:**

Build specific DTB:

.. code-block:: bash

   adibuild linux dtbs -p zynqmp zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

Build multiple DTBs:

.. code-block:: bash

   adibuild linux dtbs -p zynq \
       zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb \
       zynq-zc702-adv7511-ad9364-fmcomms4.dtb

Build all configured DTBs:

.. code-block:: bash

   adibuild linux dtbs -p zynqmp

Clean Command
~~~~~~~~~~~~~

Clean kernel build artifacts.

.. code-block:: bash

   adibuild linux clean [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Target platform

.. option:: --tag TAG, -t TAG

   Git tag or branch

.. option:: --deep

   Deep clean (runs ``make mrproper`` instead of ``make clean``)

**Examples:**

Regular clean:

.. code-block:: bash

   adibuild linux clean -p zynqmp -t 2023_R2

Deep clean (removes .config):

.. code-block:: bash

   adibuild linux clean -p zynq -t 2023_R2 --deep

libad9361-iio Commands
----------------------

Build Command
~~~~~~~~~~~~~

Build the libad9361-iio library for the specified platform.

.. code-block:: bash

   adibuild libad9361 build [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config (e.g., ``arm``, ``arm64``, ``native``).

.. option:: --tag TAG, -t TAG

   Git tag or branch to build (e.g., ``main``, ``2023_R2``).

.. option:: --arch ARCH

   Target architecture (overrides config).

.. option:: --libiio-path PATH

   Path to cross-compiled libiio installation (must contain ``include/`` and ``lib/``).

.. option:: --clean

   Remove build directory before building.

.. option:: --jobs N, -j N

   Number of parallel make jobs.

.. option:: --generate-script

   Generate a bash build script instead of executing the build.

**Examples:**

Build for ARM:

.. code-block:: bash

   adibuild --config configs/libad9361/default.yaml libad9361 build -p arm

Clean Command
~~~~~~~~~~~~~

Remove libad9361-iio build artifacts.

.. code-block:: bash

   adibuild libad9361 clean [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config.

.. option:: --tag TAG, -t TAG

   Git tag or branch.

.. option:: --deep

   Remove the entire build directory.

Genalyzer Commands
------------------

Build Command
~~~~~~~~~~~~~

Build the genalyzer DSP analysis library.

.. code-block:: bash

   adibuild genalyzer build [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config (e.g., ``arm``, ``arm64``, ``native``).

.. option:: --tag TAG, -t TAG

   Git tag or branch to build (e.g., ``main``, ``v0.1.2``).

.. option:: --arch ARCH

   Target architecture (overrides config).

.. option:: --fftw-path PATH

   Path to pre-built FFTW3 installation (must contain ``include/`` and ``lib/``).
   Required for cross-compiled targets.

.. option:: --clean

   Remove build directory before building.

.. option:: --jobs N, -j N

   Number of parallel make jobs.

.. option:: --generate-script

   Generate a bash build script instead of executing the build.

**Examples:**

Build natively:

.. code-block:: bash

   adibuild --config configs/genalyzer/default.yaml genalyzer build -p native

Build for ARM64 with custom FFTW3:

.. code-block:: bash

   adibuild --config configs/genalyzer/default.yaml genalyzer build -p arm64 \
     --fftw-path /opt/fftw3-arm64

Clean Command
~~~~~~~~~~~~~

Remove genalyzer build artifacts.

.. code-block:: bash

   adibuild genalyzer clean [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   **Required.** Platform name from config.

.. option:: --tag TAG, -t TAG

   Git tag or branch.

.. option:: --deep

   Remove the entire build directory.

Toolchain Command
-----------------

Detect and display available toolchains.

.. code-block:: bash

   adibuild toolchain [OPTIONS]

Options:

.. option:: --platform PLATFORM, -p PLATFORM

   Show toolchain that would be selected for specific platform

**Example:**

Show all available toolchains:

.. code-block:: bash

   adibuild toolchain

**Output:**

.. code-block:: text

   Detecting available toolchains...

   ✓ Vivado/Vitis Toolchain:
     ARM32: /opt/Xilinx/Vitis/2023.2/gnu/aarch32/lin/gcc-arm-linux-gnueabi
     ARM64: /opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux/bin/aarch64-xilinx-linux-gnu-gcc
     Version: 12.2.0

   ✗ ARM GNU toolchain not found (can be auto-downloaded)

   ✗ System cross-compiler not found

Show toolchain for specific platform:

.. code-block:: bash

   adibuild toolchain -p zynqmp

**Output:**

.. code-block:: text

   [Selected for zynqmp]
   Type: vivado
   Path: /opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux
   Cross-compile: aarch64-xilinx-linux-gnu-
   Version: 12.2.0

Configuration Commands
----------------------

Config Init
~~~~~~~~~~~

Initialize global configuration file.

.. code-block:: bash

   adibuild config init

Creates ``~/.adibuild/config.yaml`` with default settings.

**Example:**

.. code-block:: bash

   adibuild config init

**Output:**

.. code-block:: text

   Created global configuration: /home/user/.adibuild/config.yaml

Config Validate
~~~~~~~~~~~~~~~

Validate configuration file against schema.

.. code-block:: bash

   adibuild config validate CONFIG_FILE

**Example:**

.. code-block:: bash

   adibuild config validate my_config.yaml

**Output:**

.. code-block:: text

   Validating configuration: my_config.yaml
   ✓ YAML syntax valid
   ✓ Required fields present
   ✓ Platform configuration valid
   Configuration is valid!

Config Show
~~~~~~~~~~~

Display configuration and available platforms.

.. code-block:: bash

   adibuild config show [OPTIONS]

Options:

.. option:: --config PATH, -c PATH

   Configuration file to show (default: ``configs/linux/2023_R2.yaml``)

**Example:**

.. code-block:: bash

   adibuild config show

**Output:**

.. code-block:: text

   Project: linux
   Repository: https://github.com/analogdevicesinc/linux.git
   Tag: 2023_R2

   Available Platforms:
   - zynq (arm)
   - zynqmp (arm64)

   Platform 'zynqmp':
     Architecture: arm64
     Defconfig: adi_zynqmp_defconfig
     Kernel Target: Image
     DTBs: 6 configured

Common Workflows
----------------

First-Time Build
~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Check available toolchains
   adibuild toolchain

   # 2. View available platforms
   adibuild config show

   # 3. Build kernel
   adibuild linux build -p zynqmp -t 2023_R2

Customized Kernel Build
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Run menuconfig
   adibuild linux menuconfig -p zynqmp -t 2023_R2

   # 2. Make configuration changes, save and exit

   # 3. Build with custom config
   adibuild linux build -p zynqmp -t 2023_R2

Clean and Rebuild
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Deep clean
   adibuild linux clean -p zynqmp -t 2023_R2 --deep

   # Rebuild from scratch
   adibuild linux build -p zynqmp -t 2023_R2 --clean

Build for Multiple Platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Build for Zynq (ARM32)
   adibuild linux build -p zynq -t 2023_R2

   # Build for ZynqMP (ARM64)
   adibuild linux build -p zynqmp -t 2023_R2

Custom Configuration Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # 1. Create custom config
   cp configs/linux/2023_R2.yaml my_config.yaml

   # 2. Edit my_config.yaml
   nano my_config.yaml

   # 3. Validate
   adibuild config validate my_config.yaml

   # 4. Build with custom config
   adibuild --config my_config.yaml linux build -p zynqmp

CI/CD Build
~~~~~~~~~~~

.. code-block:: bash

   # Clean build with maximum parallelism
   adibuild -v linux build -p zynqmp -t 2023_R2 --clean -j $(nproc)

Environment Variables
---------------------

pyadi-build respects these environment variables:

.. envvar:: XILINX_VIVADO

   Path to Xilinx Vivado installation (e.g., ``/opt/Xilinx/Vivado/2023.2``)

.. envvar:: XILINX_VITIS

   Path to Xilinx Vitis installation (e.g., ``/opt/Xilinx/Vitis/2023.2``)

.. envvar:: ADIBUILD_CONFIG

   Default configuration file path

.. envvar:: ADIBUILD_CACHE_DIR

   Cache directory for toolchains and repositories (default: ``~/.adibuild``)

**Example:**

.. code-block:: bash

   export XILINX_VITIS=/opt/Xilinx/Vitis/2023.2
   adibuild linux build -p zynqmp -t 2023_R2

Exit Codes
----------

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Code
     - Meaning
   * - 0
     - Success
   * - 1
     - Build error (compilation failed, toolchain not found, etc.)
   * - 2
     - Invalid arguments or configuration

Shell Completion
----------------

Enable shell completion for bash, zsh, or fish:

**Bash:**

.. code-block:: bash

   eval "$(_ADIBUILD_COMPLETE=bash_source adibuild)"

Add to ``~/.bashrc`` for permanent activation.

**Zsh:**

.. code-block:: bash

   eval "$(_ADIBUILD_COMPLETE=zsh_source adibuild)"

Add to ``~/.zshrc`` for permanent activation.

**Fish:**

.. code-block:: bash

   eval (env _ADIBUILD_COMPLETE=fish_source adibuild)

Add to ``~/.config/fish/config.fish`` for permanent activation.

Tips and Tricks
---------------

Faster Builds
~~~~~~~~~~~~~

.. code-block:: bash

   # Use all CPU cores
   adibuild linux build -p zynqmp -t 2023_R2 -j $(nproc)


   # Use tmpfs for faster I/O
   adibuild linux build -p zynqmp -t 2023_R2 -o /tmp/build

Generate Portable Build Scripts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can generate a bash script to run the build later or on another machine:

.. code-block:: bash

   # Generate script for ZynqMP
   adibuild linux build -p zynqmp -t 2023_R2 --generate-script

   # Run the generated script
   bash ~/.adibuild/work/build_linux_arm64.sh

Debugging Build Issues
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Enable maximum verbosity
   adibuild -vv linux build -p zynqmp -t 2023_R2

   # Check build log
   cat ~/.adibuild/work/build-arm64.log

Shallow Clone for Faster Initial Setup
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a config with shallow clone:

.. code-block:: yaml

   repository_options:
     depth: 1
     single_branch: true

.. code-block:: bash

   adibuild --config shallow_config.yaml linux build -p zynqmp -t 2023_R2

Build Specific Boards Only
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a config with only the DTBs you need:

.. code-block:: yaml

   platforms:
     zynqmp:
       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

This reduces build time by skipping unnecessary DTBs.

Next Steps
----------

- Learn about :doc:`python-api-usage` for programmatic builds
- See :doc:`configuration-guide` for complete configuration reference
- Check :doc:`toolchain-management` for toolchain details
- Explore :doc:`platforms` for platform-specific information
