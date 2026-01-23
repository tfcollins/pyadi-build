Quick Start
===========

Get started with pyadi-build in minutes! This guide will walk you through your first kernel build.

.. note::
   Make sure you've completed the :doc:`installation` before proceeding.

First Build
-----------

Step 1: Check Available Toolchains
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before building, check what toolchains are available:

.. code-block:: bash

   adibuild toolchain

This will detect:

- Xilinx Vivado/Vitis toolchains
- Cached ARM GNU toolchains
- System-installed cross-compilers

.. tip::
   Don't worry if none are found! The ARM GNU toolchain will be automatically downloaded
   when you run your first build.

Step 2: View Available Platforms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

See what platforms you can build for:

.. code-block:: bash

   adibuild config show

This shows:

- Available platforms (``zynq``, ``zynqmp``)
- Their configurations
- Device tree blobs (DTBs)

Step 3: Build Your First Kernel
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For ZynqMP (ARM64)
^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

This will:

1. Clone the ADI Linux kernel repository
2. Checkout the 2023_R2 tag
3. Download the ARM64 toolchain (if needed)
4. Configure the kernel with ``adi_zynqmp_defconfig``
5. Build the kernel and device trees
6. Package artifacts in ``build/linux-2023_R2-arm64/``

For Zynq (ARM32)
^^^^^^^^^^^^^^^^

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2

This builds for the Zynq platform (ARM Cortex-A9).

Step 4: Find Your Build Artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After a successful build, find your artifacts:

.. code-block:: bash

   ls -l build/linux-2023_R2-*/

Output structure:

.. code-block:: text

   build/linux-2023_R2-arm64/
   ├── Image                    # Kernel image
   ├── dts/                     # Device tree blobs
   │   ├── zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   │   ├── zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
   │   └── ...
   └── metadata.json            # Build information

Common Tasks
------------

Build with Custom Options
~~~~~~~~~~~~~~~~~~~~~~~~~~

Use more parallel jobs:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 -j 16

Clean before building:

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2 --clean

Build only device trees:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 --dtbs-only

Interactive Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~

Run ``menuconfig`` to customize the kernel:

.. code-block:: bash

   adibuild linux menuconfig -p zynqmp -t 2023_R2

This opens the interactive kernel configuration interface. After making changes,
build with your custom configuration:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

Build Specific DTBs
~~~~~~~~~~~~~~~~~~~

Build only specific device tree blobs:

.. code-block:: bash

   adibuild linux dtbs -p zynq -t 2023_R2 \
       zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb

Clean Build Artifacts
~~~~~~~~~~~~~~~~~~~~~~

Regular clean (removes build artifacts):

.. code-block:: bash

   adibuild linux clean -p zynq -t 2023_R2

Deep clean (``mrproper`` - removes configuration too):

.. code-block:: bash

   adibuild linux clean -p zynq -t 2023_R2 --deep

Using the Python API
--------------------

You can also use pyadi-build as a Python library. Create a file ``build_kernel.py``:

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqMPPlatform

   # Load configuration
   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # Get platform configuration
   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)

   # Create builder and build
   builder = LinuxBuilder(config, platform)
   result = builder.build()

   print(f"Build completed in {result['duration']:.1f}s")
   print(f"Output: {result['artifacts']}")

Run it:

.. code-block:: bash

   python build_kernel.py

Configuration
-------------

Global Configuration
~~~~~~~~~~~~~~~~~~~~

Create a global configuration file:

.. code-block:: bash

   adibuild config init

This creates ``~/.adibuild/config.yaml`` where you can set:

- Default parallel jobs
- Vivado path (if not auto-detected)
- Toolchain cache directory

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

Create your own configuration file ``my_config.yaml``:

.. code-block:: yaml

   project: linux
   repository: https://github.com/analogdevicesinc/linux.git
   tag: 2023_R2

   build:
     parallel_jobs: 16
     output_dir: ./my_builds

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

Quick Reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Command
     - Description
   * - ``adibuild --version``
     - Show version
   * - ``adibuild toolchain``
     - Check available toolchains
   * - ``adibuild config show``
     - List available platforms
   * - ``adibuild linux build -p <platform> -t <tag>``
     - Build kernel
   * - ``adibuild linux menuconfig -p <platform>``
     - Configure kernel interactively
   * - ``adibuild linux clean -p <platform>``
     - Clean build artifacts
   * - ``adibuild -vv``
     - Enable verbose mode

Next Steps
----------

- Learn more in the :doc:`first-build` detailed walkthrough
- Understand :doc:`configuration-basics`
- Check the :doc:`../user-guide/index` for advanced usage
- Explore :doc:`../examples/index` for more code samples

Need Help?
----------

- See :doc:`troubleshooting` for common issues
- Check ``adibuild --help`` for all available commands
- Visit the `GitHub repository <https://github.com/analogdevicesinc/pyadi-build>`_
- Open an issue on the `issue tracker <https://github.com/analogdevicesinc/pyadi-build/issues>`_
