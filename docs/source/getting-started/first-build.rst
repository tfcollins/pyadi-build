First Build
===========

This guide provides a detailed walkthrough of building your first ADI Linux kernel
using pyadi-build. We'll build a kernel for the ZynqMP platform step by step.

Prerequisites
-------------

Before starting, ensure you have:

1. Completed the :doc:`installation`
2. Verified installation with ``adibuild --version``
3. A stable internet connection (for downloading repositories and toolchains)
4. At least 10 GB of free disk space

Understanding the Build Process
--------------------------------

When you run a build, pyadi-build performs these steps:

.. mermaid::

   graph TB
       A[Load Configuration] --> B[Select Platform]
       B --> C[Detect/Download Toolchain]
       C --> D[Clone/Update Repository]
       D --> E[Configure Kernel]
       E --> F[Build Kernel]
       F --> G[Build Device Trees]
       G --> H[Package Artifacts]

       style A fill:#e1f5ff
       style H fill:#c8e6c9

Let's walk through each step.

Step-by-Step Walkthrough
-------------------------

Step 1: Check System Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, verify that your system is ready:

.. code-block:: bash

   # Check Python version (should be 3.10+)
   python3 --version

   # Check Git
   git --version

   # Check Make
   make --version

   # Check pyadi-build
   adibuild --version

Expected output:

.. code-block:: text

   Python 3.11.0
   git version 2.39.0
   GNU Make 4.3
   pyadi-build version 0.1.0

Step 2: Examine Available Configurations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

List the pre-configured build options:

.. code-block:: bash

   adibuild config show

This shows available platforms and their configurations. You'll see:

- **zynq** - ARM Cortex-A9 (32-bit)
- **zynqmp** - ARM Cortex-A53 (64-bit)

Step 3: Check Toolchain Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Before building, check what toolchains are available:

.. code-block:: bash

   adibuild toolchain

Possible outputs:

**Scenario 1: Vivado/Vitis Found**

.. code-block:: text

   Xilinx Vivado/Vitis Toolchains:
   ✓ ARM32: /opt/Xilinx/Vitis/2023.2/gnu/aarch32/lin/gcc-arm-linux-gnueabi
   ✓ ARM64: /opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux/bin/aarch64-xilinx-linux-gnu-gcc

**Scenario 2: No Toolchains Found**

.. code-block:: text

   No Xilinx Vivado/Vitis found
   No cached ARM GNU toolchains
   System toolchains: Not found

   ARM GNU toolchain will be downloaded automatically when needed.

.. tip::
   If no toolchains are found, pyadi-build will automatically download the
   appropriate ARM GNU toolchain during the build. This is the most common scenario.

Step 4: Start Your First Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Now, let's build a kernel for the ZynqMP platform:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

Let's break down this command:

- ``adibuild`` - The main CLI command
- ``linux`` - Build a Linux kernel (vs HDL or libiio in the future)
- ``build`` - Perform a full build
- ``-p zynqmp`` - Target the ZynqMP platform (ARM64)
- ``-t 2023_R2`` - Use the 2023_R2 release tag

What Happens During the Build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You'll see progress through these stages:

**Stage 1: Loading Configuration**

.. code-block:: text

   Loading configuration from configs/linux/2023_R2.yaml
   Platform: zynqmp (arm64)

**Stage 2: Repository Management**

.. code-block:: text

   Checking repository: https://github.com/analogdevicesinc/linux.git
   Cloning into '/home/user/.adibuild/work/linux'...
   Checking out tag: 2023_R2

.. note::
   The first build clones the entire kernel repository (~4 GB). This takes several
   minutes. Subsequent builds reuse the cached repository and are much faster.

**Stage 3: Toolchain Setup**

.. code-block:: text

   Detecting toolchain for arm64...
   No Vivado toolchain found
   Downloading ARM GNU toolchain (arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu)...
   Extracting toolchain...
   Toolchain ready: aarch64-none-linux-gnu-gcc

.. note::
   The toolchain download (~120 MB) happens only once and is cached in
   ``~/.adibuild/toolchains/arm/``.

**Stage 4: Kernel Configuration**

.. code-block:: text

   Configuring kernel with adi_zynqmp_defconfig...
   HOSTCC  scripts/basic/fixdep
   HOSTCC  scripts/kconfig/conf.o
   Configuration written to .config

**Stage 5: Kernel Build**

.. code-block:: text

   Building kernel (Image) with 8 parallel jobs...
   SYNC    include/config/auto.conf.cmd
   CC      init/main.o
   CC      init/version.o
   ...
   LD      vmlinux
   OBJCOPY arch/arm64/boot/Image

**Stage 6: Device Tree Build**

.. code-block:: text

   Building device trees...
   DTC     arch/arm64/boot/dts/xilinx/zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   DTC     arch/arm64/boot/dts/xilinx/zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb

**Stage 7: Packaging**

.. code-block:: text

   Copying artifacts to build/linux-2023_R2-arm64/
   Creating metadata.json
   Build completed in 847.3s

Step 5: Examine Build Artifacts
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After the build completes, examine the output:

.. code-block:: bash

   ls -lh build/linux-2023_R2-arm64/

You should see:

.. code-block:: text

   -rw-r--r-- 1 user user  19M Jan 23 10:15 Image
   drwxr-xr-x 2 user user 4.0K Jan 23 10:15 dts
   -rw-r--r-- 1 user user  512 Jan 23 10:15 metadata.json

View the device tree blobs:

.. code-block:: bash

   ls -lh build/linux-2023_R2-arm64/dts/

.. code-block:: text

   -rw-r--r-- 1 user user  45K Jan 23 10:15 zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   -rw-r--r-- 1 user user  44K Jan 23 10:15 zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
   -rw-r--r-- 1 user user  46K Jan 23 10:15 zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb

Step 6: Inspect Build Metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

View the build metadata:

.. code-block:: bash

   cat build/linux-2023_R2-arm64/metadata.json

Example output:

.. code-block:: json

   {
     "project": "linux",
     "platform": "zynqmp",
     "architecture": "arm64",
     "tag": "2023_R2",
     "commit": "a1b2c3d4e5f6...",
     "build_date": "2024-01-23T10:15:30",
     "duration": 847.3,
     "toolchain": {
       "type": "arm",
       "version": "12.2.rel1",
       "cross_compile": "aarch64-none-linux-gnu-"
     },
     "artifacts": {
       "kernel_image": "Image",
       "dtbs": [
         "dts/zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb",
         "dts/zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb"
       ]
     }
   }

Understanding the Output
------------------------

Kernel Image
~~~~~~~~~~~~

The ``Image`` file is the compiled Linux kernel:

- **Size**: ~15-25 MB (uncompressed)
- **Format**: ARM64 raw binary image
- **Usage**: Load on ZynqMP board via U-Boot or JTAG

Device Tree Blobs
~~~~~~~~~~~~~~~~~

The ``.dtb`` files describe the hardware configuration:

- **Purpose**: Tell the kernel about board-specific hardware
- **Format**: Binary device tree
- **Usage**: Load alongside kernel on the target board

Each DTB corresponds to a different board/FMC combination:

- ``zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb`` - ZCU102 + FMCOMMS2/3
- ``zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb`` - ZCU102 + FMCOMMS4

Metadata
~~~~~~~~

The ``metadata.json`` file provides:

- Build traceability (git commit, date)
- Toolchain information (for reproducibility)
- Build performance metrics

Next Builds
-----------

Faster Rebuilds
~~~~~~~~~~~~~~~

Subsequent builds are much faster because:

1. The repository is already cloned
2. The toolchain is already downloaded
3. Only changed files are recompiled

Example incremental build:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

.. code-block:: text

   Repository already exists, updating...
   Toolchain already cached
   Building kernel with 8 parallel jobs...
   Build completed in 127.8s

Clean Build
~~~~~~~~~~~

To force a clean build:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2 --clean

This runs ``make clean`` before building.

Building for Zynq
~~~~~~~~~~~~~~~~~

To build for the 32-bit Zynq platform:

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2

This produces a ``uImage`` file instead of ``Image``.

Troubleshooting
---------------

Build Takes Too Long
~~~~~~~~~~~~~~~~~~~~

The first build can take 10-30 minutes depending on your system. Speed it up:

.. code-block:: bash

   # Use more parallel jobs (adjust based on your CPU cores)
   adibuild linux build -p zynqmp -t 2023_R2 -j 16

Repository Clone is Slow
~~~~~~~~~~~~~~~~~~~~~~~~~

For faster initial setup, use a shallow clone. Create a custom config:

.. code-block:: yaml

   repository_options:
     depth: 1  # Only download latest commit

Toolchain Download Fails
~~~~~~~~~~~~~~~~~~~~~~~~~

If the automatic download fails, install a system toolchain:

.. code-block:: bash

   # Ubuntu/Debian
   sudo apt install gcc-aarch64-linux-gnu

   # Then rebuild
   adibuild linux build -p zynqmp -t 2023_R2

Out of Disk Space
~~~~~~~~~~~~~~~~~

The kernel repository and build artifacts require ~10 GB. To clean up:

.. code-block:: bash

   # Remove build artifacts
   adibuild linux clean -p zynqmp -t 2023_R2 --deep

   # Remove cached repository (will be re-cloned)
   rm -rf ~/.adibuild/work/linux

Next Steps
----------

Congratulations! You've successfully built your first ADI Linux kernel. Next:

- Learn about :doc:`configuration-basics` to customize builds
- Explore the :doc:`../user-guide/cli-usage` for all CLI options
- Try the :doc:`../user-guide/python-api-usage` for programmatic builds
- See :doc:`../examples/index` for more advanced usage patterns
