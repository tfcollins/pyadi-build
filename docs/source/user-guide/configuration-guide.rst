Configuration Guide
===================

This guide provides a complete reference for pyadi-build YAML configuration files.

Configuration File Structure
-----------------------------

A complete configuration file has these top-level sections:

.. code-block:: yaml

   # Project information
   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   # Build settings
   build:
     parallel_jobs: 8
     clean_before: false
     output_dir: ./build

   # Platform configurations
   platforms:
     zynq:
       # Zynq platform settings
     zynqmp:
       # ZynqMP platform settings

   # Repository options
   repository_options:
     depth: null
     single_branch: false

   # Global settings (optional)
   vivado:
     install_path: /opt/Xilinx/Vitis/2023.2

Project Section
---------------

Defines what project to build.

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

**Fields:**

.. describe:: project

   :Type: string
   :Required: Yes
   :Values: ``linux``, ``hdl``

   Project type to build.

.. describe:: repository

   :Type: string (URL)
   :Required: Yes

   Git repository URL. Can be HTTPS or SSH.

   **Examples:**

   .. code-block:: yaml

      # HTTPS
      repository: https://github.com/analogdevicesinc/linux.git

      # SSH
      repository: git@github.com:analogdevicesinc/linux.git

.. describe:: tag

   :Type: string
   :Required: Yes

   Git tag, branch, or commit to build.

   **Examples:**

   .. code-block:: yaml

      # Release tag
      tag: 2023_R2

      # Branch
      tag: main

      # Commit SHA
      tag: a1b2c3d4e5f6...

Build Section
-------------

Configures build behavior.

.. code-block:: yaml

   build:
     parallel_jobs: 8
     clean_before: false
     output_dir: ./build

**Fields:**

.. describe:: parallel_jobs

   :Type: integer
   :Default: Number of CPU cores
   :Range: 1-256

   Number of parallel make jobs.

   .. tip::
      Set to the number of CPU cores for optimal performance:

      .. code-block:: bash

         nproc  # Linux
         sysctl -n hw.ncpu  # macOS

.. describe:: clean_before

   :Type: boolean
   :Default: false

   Run ``make clean`` before building.

.. describe:: output_dir

   :Type: string (path)
   :Default: ``./build``

   Directory for build artifacts. Can be relative or absolute.

   **Examples:**

   .. code-block:: yaml

      # Relative to current directory
      output_dir: ./build

      # Absolute path
      output_dir: /tmp/kernel-builds

      # User home directory
      output_dir: ~/builds

Platform Section
----------------

Each platform has its own configuration under the ``platforms`` key.

Platform Configuration
~~~~~~~~~~~~~~~~~~~~~~

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

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

     zed_fmcomms2:
       hdl_project: fmcomms2
       carrier: zed
       arch: arm
       make_variables:
         RX_LANE_RATE: 2.5

**Fields (Linux):**

.. describe:: arch

   :Type: string
   :Required: Yes
   :Values: ``arm``, ``arm64``

   Target architecture.

.. describe:: cross_compile

   :Type: string
   :Required: Yes

   Toolchain prefix (``CROSS_COMPILE`` variable for kernel Makefile).

   **Examples:**

   .. code-block:: yaml

      # ARM32
      cross_compile: arm-linux-gnueabihf-

      # ARM64
      cross_compile: aarch64-linux-gnu-

      # Xilinx ARM64
      cross_compile: aarch64-xilinx-linux-gnu-

.. describe:: defconfig

   :Type: string
   :Required: Yes

   Default kernel configuration file.

   **Examples:**

   .. code-block:: yaml

      # ZynqMP
      defconfig: adi_zynqmp_defconfig

      # Zynq
      defconfig: zynq_xcomm_adv7511_defconfig

.. describe:: kernel_target

   :Type: string
   :Required: Yes

   Kernel make target.

   **Examples:**

   .. code-block:: yaml

      # ARM64
      kernel_target: Image

      # ARM32 with U-Boot header
      kernel_target: uImage

.. describe:: dtb_path

   :Type: string
   :Required: Yes

   Path to device tree blobs within kernel source.

   **Examples:**

   .. code-block:: yaml

      # ZynqMP
      dtb_path: arch/arm64/boot/dts/xilinx

      # Zynq
      dtb_path: arch/arm/boot/dts

.. describe:: kernel_image_path

   :Type: string
   :Required: Yes

   Path to kernel image within kernel source.

   **Examples:**

   .. code-block:: yaml

      # ARM64
      kernel_image_path: arch/arm64/boot/Image

      # ARM32
      kernel_image_path: arch/arm/boot/uImage

**Fields (HDL):**

.. describe:: hdl_project

   :Type: string
   :Required: Yes (for HDL)

   HDL project name (e.g., ``fmcomms2``, ``daq2``).

.. describe:: carrier

   :Type: string
   :Required: Yes (for HDL)

   Carrier board name (e.g., ``zed``, ``zcu102``).

.. describe:: make_variables

   :Type: dictionary
   :Required: No

   Variables to pass to make command.

   **Example:**

   .. code-block:: yaml

      make_variables:
        RX_LANE_RATE: 2.5
        JESD_MODE: 64T64R

Device Tree Blobs
~~~~~~~~~~~~~~~~~

.. describe:: dtbs

   :Type: list of strings
   :Required: No
   :Default: Empty list (build all)

   List of device tree blobs to build.

   **Examples:**

   .. code-block:: yaml

      # Build specific DTBs
      dtbs:
        - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
        - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb

      # Build all DTBs
      dtbs: []

Toolchain Configuration
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   toolchain:
     preferred: vivado
     fallback:
       - arm
       - system

.. describe:: preferred

   :Type: string
   :Values: ``vivado``, ``arm``, ``system``

   Preferred toolchain type.

.. describe:: fallback

   :Type: list of strings
   :Values: ``vivado``, ``arm``, ``system``

   Ordered list of fallback toolchains if preferred is not available.

**Toolchain Types:**

- **vivado**: Xilinx Vivado/Vitis bundled toolchains
- **arm**: ARM GNU toolchains (auto-downloaded)
- **system**: System-installed cross-compilers

Repository Options
------------------

Controls git clone behavior.

.. code-block:: yaml

   repository_options:
     depth: null
     single_branch: false

**Fields:**

.. describe:: depth

   :Type: integer or null
   :Default: null (full clone)

   Number of commits to fetch. Set to 1 for shallow clone.

   **Examples:**

   .. code-block:: yaml

      # Full clone (~4 GB)
      depth: null

      # Shallow clone (~500 MB)
      depth: 1

.. describe:: single_branch

   :Type: boolean
   :Default: false

   Clone only the specified branch/tag.

Global Settings (Optional)
---------------------------

Vivado Settings
~~~~~~~~~~~~~~~

.. code-block:: yaml

   vivado:
     install_path: /opt/Xilinx/Vitis/2023.2

.. describe:: install_path

   :Type: string (path)
   :Required: No

   Path to Vivado/Vitis installation. If not specified, auto-detected from:

   - ``XILINX_VIVADO`` environment variable
   - ``XILINX_VITIS`` environment variable
   - Common installation paths

Complete Configuration Examples
--------------------------------

ZynqMP Configuration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   build:
     parallel_jobs: 16
     clean_before: false
     output_dir: ./build

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

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

   repository_options:
     depth: null
     single_branch: false

Zynq Configuration
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   build:
     parallel_jobs: 8
     output_dir: ./build

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
         - zynq-zc706-adv7511-ad9364-fmcomms4.dtb

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

CI/CD Optimized Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   build:
     parallel_jobs: 4  # Limited CI resources
     clean_before: true  # Always start clean
     output_dir: ./ci-build

   platforms:
     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtb_path: arch/arm64/boot/dts/xilinx
       kernel_image_path: arch/arm64/boot/Image

       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb  # Single DTB for speed

       toolchain:
         preferred: arm  # ARM GNU auto-download
         fallback: []

   repository_options:
     depth: 1  # Shallow clone for speed
     single_branch: true

Development Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: main  # Development branch

   build:
     parallel_jobs: 16
     output_dir: /tmp/dev-build  # Fast tmpfs

   platforms:
     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtb_path: arch/arm64/boot/dts/xilinx
       kernel_image_path: arch/arm64/boot/Image

       dtbs: []  # Build all DTBs

       toolchain:
         preferred: vivado
         fallback:
           - system

   repository_options:
     depth: null  # Full history for development
     single_branch: false

Configuration Validation
------------------------

Schema Validation
~~~~~~~~~~~~~~~~~

Validate against JSON schema:

.. code-block:: bash

   adibuild config validate my_config.yaml

The validator checks:

- YAML syntax
- Required fields present
- Valid field types
- Valid enum values
- Platform configuration completeness

Manual Validation
~~~~~~~~~~~~~~~~~

Check configuration programmatically:

.. code-block:: python

   from adibuild import BuildConfig

   try:
       config = BuildConfig.from_yaml('my_config.yaml')
       print("Configuration is valid")
   except Exception as e:
       print(f"Configuration error: {e}")

Configuration Best Practices
-----------------------------

1. **Start with defaults**: Copy and modify ``configs/linux/2023_R2.yaml``

2. **Validate early**: Always validate before using:

   .. code-block:: bash

      adibuild config validate my_config.yaml

3. **Use version control**: Track configuration files in git

4. **Document changes**: Add comments explaining modifications

5. **Test locally first**: Validate configuration locally before CI/CD

6. **Keep platform-specific**: Separate configs for different platforms

7. **Use shallow clones**: For CI/CD, use ``depth: 1`` to save time

8. **Optimize parallel jobs**: Match to available CPU cores

Common Configuration Patterns
------------------------------

Single DTB Build
~~~~~~~~~~~~~~~~

.. code-block:: yaml

   platforms:
     zynqmp:
       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

Multiple Platforms
~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   platforms:
     zynq:
       arch: arm
       # ... zynq settings

     zynqmp:
       arch: arm64
       # ... zynqmp settings

Fast Development Builds
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   build:
     parallel_jobs: 32
     output_dir: /dev/shm/build  # RAM disk

   repository_options:
     depth: 1
     single_branch: true

Custom Toolchain Path
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   vivado:
     install_path: /custom/path/to/Vivado/2023.2

   platforms:
     zynqmp:
       toolchain:
         preferred: vivado

Next Steps
----------

- See :doc:`cli-usage` for using configurations with the CLI
- Learn about :doc:`toolchain-management` for toolchain details
- Check :doc:`platforms` for platform-specific configuration
