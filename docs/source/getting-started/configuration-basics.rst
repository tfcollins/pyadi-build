Configuration Basics
====================

This guide introduces the essential concepts for configuring pyadi-build.

Configuration Overview
----------------------

pyadi-build uses YAML files to configure builds. There are two types of configuration:

1. **Project Configuration** - Defines what to build (kernel version, platforms, DTBs)
2. **Global Configuration** - User preferences (parallel jobs, toolchain paths)

Configuration Files
-------------------

Default Configuration Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pre-configured files are available in ``configs/linux/``:

.. code-block:: bash

   configs/linux/
   ├── 2023_R2.yaml          # Full configuration for 2023_R2 release
   ├── zynq.yaml             # Zynq platform defaults
   └── zynqmp.yaml           # ZynqMP platform defaults

Using a default configuration:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

This automatically loads ``configs/linux/2023_R2.yaml``.

Global Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a user configuration at ``~/.adibuild/config.yaml``:

.. code-block:: bash

   adibuild config init

This file stores user preferences that apply to all builds.

Configuration Structure
-----------------------

A typical configuration file has four main sections:

.. code-block:: yaml

   # 1. Project information
   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   # 2. Build settings
   build:
     parallel_jobs: 8
     clean_before: false
     output_dir: ./build

   # 3. Platform configurations
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

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

   # 4. Repository options
   repository_options:
     depth: null  # Full clone (use 1 for shallow)
     single_branch: false

Let's explore each section.

Project Information
-------------------

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

- **project**: Project type (``linux``, future: ``hdl``, ``libiio``)
- **repository**: Git repository URL
- **tag**: Git tag, branch, or commit to build

Example variations:

.. code-block:: yaml

   # Use a specific branch
   tag: main

   # Use a specific commit
   tag: a1b2c3d4e5f6...

   # Use a different repository
   repository: https://github.com/torvalds/linux.git
   tag: v6.6

Build Settings
--------------

.. code-block:: yaml

   build:
     parallel_jobs: 8
     clean_before: false
     output_dir: ./build

- **parallel_jobs**: Number of parallel make jobs (default: number of CPU cores)
- **clean_before**: Run ``make clean`` before building (default: ``false``)
- **output_dir**: Where to place build artifacts (default: ``./build``)

.. tip::
   Set ``parallel_jobs`` to the number of CPU cores for optimal performance:

   .. code-block:: bash

      # Find number of cores
      nproc

Platform Configuration
----------------------

Each platform (``zynq``, ``zynqmp``) has specific settings:

.. code-block:: yaml

   platforms:
     zynqmp:
       arch: arm64                              # Target architecture
       cross_compile: aarch64-linux-gnu-        # Toolchain prefix
       defconfig: adi_zynqmp_defconfig          # Default kernel config
       kernel_target: Image                     # Make target
       dtb_path: arch/arm64/boot/dts/xilinx     # DTB location
       kernel_image_path: arch/arm64/boot/Image # Kernel image location

       dtbs:                                    # Device trees to build
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
         - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb

       toolchain:                               # Toolchain preferences
         preferred: vivado
         fallback:
           - arm
           - system

Key Fields Explained
~~~~~~~~~~~~~~~~~~~~

**arch**
   Target architecture (``arm`` for Zynq, ``arm64`` for ZynqMP)

**cross_compile**
   Toolchain prefix passed to the kernel Makefile

**defconfig**
   Default kernel configuration file to use

**kernel_target**
   Make target for the kernel (``uImage`` for Zynq, ``Image`` for ZynqMP)

**dtbs**
   List of device tree blobs to build

**toolchain**
   Toolchain selection strategy:

   - **preferred**: ``vivado``, ``arm``, or ``system``
   - **fallback**: List of alternatives if preferred is unavailable

Toolchain Configuration
-----------------------

Toolchain Preference Order
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   toolchain:
     preferred: vivado
     fallback:
       - arm
       - system

pyadi-build tries toolchains in this order:

1. **vivado** - Xilinx Vivado/Vitis bundled toolchains
2. **arm** - ARM GNU toolchain (auto-downloaded)
3. **system** - System-installed cross-compilers

If the preferred toolchain isn't found, it falls back to the next option.

Specifying Vivado Path
~~~~~~~~~~~~~~~~~~~~~~~

If Vivado isn't auto-detected, specify the path:

.. code-block:: yaml

   vivado:
     install_path: /opt/Xilinx/Vitis/2023.2

Or set environment variables:

.. code-block:: bash

   export XILINX_VIVADO=/opt/Xilinx/Vivado/2023.2
   export XILINX_VITIS=/opt/Xilinx/Vitis/2023.2

Forcing a Specific Toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use only the ARM GNU toolchain:

.. code-block:: yaml

   toolchain:
     preferred: arm
     fallback: []  # No fallback

Device Tree Configuration
-------------------------

Specify which DTBs to build:

.. code-block:: yaml

   dtbs:
     - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
     - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
     - zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb

Build only specific boards:

.. code-block:: yaml

   dtbs:
     - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb  # Only FMCOMMS2/3

Build all available DTBs:

.. code-block:: yaml

   dtbs: []  # Empty list means build all

Repository Options
------------------

Control how the repository is cloned:

.. code-block:: yaml

   repository_options:
     depth: 1              # Shallow clone (faster, smaller)
     single_branch: true   # Clone only the specified branch

**depth**
   Number of commits to fetch:

   - ``null`` - Full history (default)
   - ``1`` - Only latest commit (shallow clone)

**single_branch**
   Whether to clone only the target branch:

   - ``false`` - Clone all branches (default)
   - ``true`` - Clone only the specified tag/branch

.. tip::
   For faster initial clones, use shallow clones:

   .. code-block:: yaml

      repository_options:
        depth: 1
        single_branch: true

   This reduces download size from ~4 GB to ~500 MB.

Creating Custom Configurations
-------------------------------

Basic Custom Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create ``my_config.yaml``:

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   build:
     parallel_jobs: 16
     output_dir: ./custom_builds

   platforms:
     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

Use it:

.. code-block:: bash

   adibuild --config my_config.yaml linux build -p zynqmp

Extending Default Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Start with a default config and modify it:

.. code-block:: bash

   # Copy default config
   cp configs/linux/2023_R2.yaml my_config.yaml

   # Edit my_config.yaml
   nano my_config.yaml

   # Use modified config
   adibuild --config my_config.yaml linux build -p zynqmp

Multiple Platforms
~~~~~~~~~~~~~~~~~~

Configure multiple platforms in one file:

.. code-block:: yaml

   platforms:
     zynq:
       arch: arm
       cross_compile: arm-linux-gnueabihf-
       defconfig: zynq_xcomm_adv7511_defconfig
       kernel_target: uImage
       dtbs:
         - zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb

     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

Build for different platforms:

.. code-block:: bash

   adibuild --config my_config.yaml linux build -p zynq
   adibuild --config my_config.yaml linux build -p zynqmp

Configuration Validation
------------------------

Validate a configuration file:

.. code-block:: bash

   adibuild config validate my_config.yaml

This checks:

- YAML syntax
- Required fields present
- Valid values for enums
- Platform configuration completeness

Example output:

.. code-block:: text

   Validating configuration: my_config.yaml
   ✓ YAML syntax valid
   ✓ Required fields present
   ✓ Platform 'zynqmp' configuration valid
   ✓ Toolchain configuration valid

   Configuration is valid!

View Configuration
------------------

Display loaded configuration:

.. code-block:: bash

   adibuild config show

Example output:

.. code-block:: yaml

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

Configuration Precedence
-------------------------

Configuration is loaded in this order (later overrides earlier):

1. Default configuration (``configs/linux/<tag>.yaml``)
2. Global configuration (``~/.adibuild/config.yaml``)
3. Custom configuration (``--config my_config.yaml``)
4. Command-line options (``-j 16``, ``--clean``, etc.)

Example:

.. code-block:: bash

   # Uses 8 jobs from config
   adibuild linux build -p zynqmp

   # Overrides with 16 jobs
   adibuild linux build -p zynqmp -j 16

Best Practices
--------------

1. **Start with defaults** - Use provided configurations as templates
2. **Use global config** - Store user preferences in ``~/.adibuild/config.yaml``
3. **Validate configurations** - Run ``adibuild config validate`` before using
4. **Version control** - Keep custom configs in version control
5. **Document changes** - Add comments to custom configurations

Common Patterns
---------------

High-Performance Build
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   build:
     parallel_jobs: 32  # Use all cores
     output_dir: /tmp/build  # Fast temporary storage

Minimal Build
~~~~~~~~~~~~~

.. code-block:: yaml

   platforms:
     zynqmp:
       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb  # Single DTB

   repository_options:
     depth: 1  # Shallow clone

CI/CD Build
~~~~~~~~~~~

.. code-block:: yaml

   build:
     clean_before: true  # Always start clean
     parallel_jobs: 4    # Limited resources

   repository_options:
     depth: 1
     single_branch: true

Next Steps
----------

- See :doc:`../user-guide/configuration-guide` for complete reference
- Learn about :doc:`../user-guide/toolchain-management`
- Explore :doc:`../user-guide/platforms` for platform-specific details
