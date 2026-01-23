Toolchain Management
====================

This guide explains how pyadi-build manages cross-compilation toolchains.

Overview
--------

pyadi-build supports three types of toolchains:

1. **Xilinx Vivado/Vitis** - Bundled with Vivado/Vitis installations
2. **ARM GNU Toolchain** - Auto-downloaded from ARM
3. **System Toolchain** - System-installed cross-compilers

Toolchains are automatically selected based on availability and configuration preferences.

Toolchain Types
---------------

1. Xilinx Vivado/Vitis Toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Advantages:**

- Officially supported by Xilinx
- Matches Vivado GCC version
- No additional downloads required
- Includes additional Xilinx tools

**Detection:**

pyadi-build automatically detects Vivado/Vitis from:

- ``XILINX_VIVADO`` environment variable
- ``XILINX_VITIS`` environment variable
- Common installation paths:

  - ``/opt/Xilinx/Vitis/``
  - ``/opt/Xilinx/Vivado/``
  - ``/tools/Xilinx/Vitis/``
  - ``/tools/Xilinx/Vivado/``

**Toolchain Locations:**

For ARM32 (Zynq):

.. code-block:: text

   ${XILINX_VITIS}/gnu/aarch32/lin/gcc-arm-linux-gnueabi/bin/arm-linux-gnueabihf-gcc

For ARM64 (ZynqMP):

.. code-block:: text

   ${XILINX_VITIS}/aarch64-xilinx-linux/bin/aarch64-xilinx-linux-gnu-gcc

**Manual Configuration:**

Set environment variable:

.. code-block:: bash

   export XILINX_VITIS=/opt/Xilinx/Vitis/2023.2

Or in configuration:

.. code-block:: yaml

   vivado:
     install_path: /opt/Xilinx/Vitis/2023.2

2. ARM GNU Toolchain
~~~~~~~~~~~~~~~~~~~~

**Advantages:**

- Automatically downloaded and cached
- No Vivado installation required
- Matches Vivado GCC versions
- Lightweight (~120 MB download)

**Auto-Download:**

When no other toolchain is available, pyadi-build automatically downloads the appropriate ARM GNU toolchain:

- **ARM32**: ``arm-none-linux-gnueabihf-gcc``
- **ARM64**: ``aarch64-none-linux-gnu-gcc``

**Version Mapping:**

pyadi-build maps Vivado versions to ARM GNU releases:

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Vivado Version
     - ARM GNU Version
     - GCC Version
   * - 2023.2
     - 12.2.rel1
     - 12.2.0
   * - 2023.1
     - 12.2.rel1
     - 12.2.0
   * - 2022.2
     - 11.2-2022.02
     - 11.2.0
   * - 2022.1
     - 11.2-2022.02
     - 11.2.0

**Cache Location:**

Downloaded toolchains are cached in:

.. code-block:: text

   ~/.adibuild/toolchains/arm/

**Manual Download:**

To pre-download toolchains:

.. code-block:: bash

   mkdir -p ~/.adibuild/toolchains/arm
   cd ~/.adibuild/toolchains/arm

   # ARM64
   wget https://developer.arm.com/.../arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz
   tar xf arm-gnu-toolchain-12.2.rel1-x86_64-aarch64-none-linux-gnu.tar.xz

   # ARM32
   wget https://developer.arm.com/.../arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-linux-gnueabihf.tar.xz
   tar xf arm-gnu-toolchain-12.2.rel1-x86_64-arm-none-linux-gnueabihf.tar.xz

3. System Toolchain
~~~~~~~~~~~~~~~~~~~

**Advantages:**

- No downloads required
- Managed by system package manager
- Easy to update

**Installation:**

.. tab-set::

   .. tab-item:: Ubuntu/Debian

      .. code-block:: bash

         # ARM32
         sudo apt install gcc-arm-linux-gnueabihf g++-arm-linux-gnueabihf

         # ARM64
         sudo apt install gcc-aarch64-linux-gnu g++-aarch64-linux-gnu

   .. tab-item:: Fedora/RHEL

      .. code-block:: bash

         # ARM32
         sudo dnf install gcc-arm-linux-gnu

         # ARM64
         sudo dnf install gcc-aarch64-linux-gnu

   .. tab-item:: macOS (Homebrew)

      .. code-block:: bash

         # ARM32
         brew install arm-linux-gnueabihf-binutils

         # ARM64
         brew install aarch64-elf-gcc

**Detection:**

System toolchains are detected in PATH:

- ``arm-linux-gnueabihf-gcc`` (ARM32)
- ``aarch64-linux-gnu-gcc`` (ARM64)

Toolchain Selection
-------------------

Selection Order
~~~~~~~~~~~~~~~

Toolchains are selected in this order:

1. **Preferred toolchain** (from configuration)
2. **First available fallback** (from configuration)
3. **Auto-download** (ARM GNU if not disabled)

**Example Configuration:**

.. code-block:: yaml

   toolchain:
     preferred: vivado
     fallback:
       - arm
       - system

Selection logic:

1. Try Vivado toolchain
2. If not found, try ARM GNU toolchain (auto-download if needed)
3. If ARM GNU fails, try system toolchain
4. If all fail, raise error

Forcing Specific Toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To use only a specific toolchain:

.. code-block:: yaml

   toolchain:
     preferred: arm
     fallback: []  # No fallbacks

Detecting Available Toolchains
-------------------------------

CLI Detection
~~~~~~~~~~~~~

.. code-block:: bash

   adibuild toolchain

**Output Example:**

.. code-block:: text

   Detecting available toolchains...

   ✓ Vivado/Vitis Toolchain:
     ARM32: /opt/Xilinx/Vitis/2023.2/gnu/aarch32/lin/gcc-arm-linux-gnueabi
     ARM64: /opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux/bin/aarch64-xilinx-linux-gnu-gcc
     Version: 12.2.0

   ✗ ARM GNU toolchain not found (can be auto-downloaded)

   ✓ System Toolchain:
     ARM64: /usr/bin/aarch64-linux-gnu-gcc
     Version: 11.4.0

Platform-Specific Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check toolchain for specific platform:

.. code-block:: bash

   adibuild toolchain -p zynqmp

**Output:**

.. code-block:: text

   [Selected for zynqmp]
   Type: vivado
   Path: /opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux
   Cross-compile: aarch64-xilinx-linux-gnu-
   Version: 12.2.0

Python API Detection
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from adibuild.core.toolchain import VivadoToolchain, ArmToolchain, SystemToolchain

   # Detect Vivado
   vivado = VivadoToolchain()
   vivado_info = vivado.detect()
   if vivado_info:
       print(f"Vivado: {vivado_info['version']}")

   # Detect ARM GNU
   arm = ArmToolchain()
   arm_info = arm.detect()
   if arm_info:
       print(f"ARM GNU: {arm_info['version']}")

   # Detect System
   system = SystemToolchain()
   system_info = system.detect()
   if system_info:
       print(f"System: {system_info['version']}")

Toolchain Versioning
--------------------

Version Detection
~~~~~~~~~~~~~~~~~

pyadi-build detects toolchain versions by running:

.. code-block:: bash

   ${CROSS_COMPILE}gcc --version

**Example Output:**

.. code-block:: text

   aarch64-xilinx-linux-gnu-gcc (GCC) 12.2.0
   Copyright (C) 2022 Free Software Foundation, Inc.

Version Requirements
~~~~~~~~~~~~~~~~~~~~

ADI Linux kernels typically require:

- **GCC 11.2+** for older kernels (2022.x tags)
- **GCC 12.2+** for newer kernels (2023.x tags)

pyadi-build automatically selects appropriate toolchain versions.

Troubleshooting
---------------

No Toolchain Found
~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error: No suitable toolchain found for arm64

**Solutions:**

1. **Let ARM GNU auto-download:**

   Just run the build - toolchain downloads automatically.

2. **Install Vivado/Vitis:**

   Set environment variable:

   .. code-block:: bash

      export XILINX_VITIS=/opt/Xilinx/Vitis/2023.2

3. **Install system toolchain:**

   .. code-block:: bash

      sudo apt install gcc-aarch64-linux-gnu

Toolchain Download Fails
~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

.. code-block:: text

   Error downloading ARM GNU toolchain

**Solutions:**

1. **Check internet connection**
2. **Download manually** (see ARM GNU Toolchain section)
3. **Use system toolchain as fallback:**

   .. code-block:: yaml

      toolchain:
        preferred: system
        fallback: []

Wrong Toolchain Version
~~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

Build fails with compiler errors due to GCC version mismatch.

**Solution:**

Specify required version in configuration:

.. code-block:: yaml

   toolchain:
     preferred: vivado  # or arm
     version: "12.2"

Toolchain Cache Issues
~~~~~~~~~~~~~~~~~~~~~~

**Problem:**

Corrupted or incomplete cached toolchain.

**Solution:**

Clear toolchain cache:

.. code-block:: bash

   rm -rf ~/.adibuild/toolchains/arm/*

The toolchain will be re-downloaded on next build.

Advanced Configuration
----------------------

Custom Toolchain Path
~~~~~~~~~~~~~~~~~~~~~

Force specific toolchain path:

.. code-block:: yaml

   platforms:
     zynqmp:
       cross_compile: /custom/path/to/aarch64-linux-gnu-

Multiple Toolchain Versions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For different kernel versions requiring different GCC versions:

**Config for 2023_R2 (GCC 12.2):**

.. code-block:: yaml

   tag: 2023_R2
   toolchain:
     preferred: vivado
     version: "12.2"

**Config for 2022_R1 (GCC 11.2):**

.. code-block:: yaml

   tag: 2022_R1
   toolchain:
     preferred: vivado
     version: "11.2"

Toolchain Caching
~~~~~~~~~~~~~~~~~

Customize cache directory:

.. code-block:: bash

   export ADIBUILD_CACHE_DIR=/custom/cache/dir

Or set in global config (``~/.adibuild/config.yaml``):

.. code-block:: yaml

   cache_dir: /custom/cache/dir

Best Practices
--------------

1. **Use Vivado toolchains** when available (most tested with ADI kernels)

2. **Let ARM GNU auto-download** for environments without Vivado

3. **Pre-download in CI/CD** to avoid network dependencies:

   .. code-block:: bash

      # In CI setup phase
      mkdir -p ~/.adibuild/toolchains/arm
      # Download and extract toolchains

4. **Version control toolchain config** for reproducible builds

5. **Test with multiple toolchains** to ensure compatibility

6. **Cache toolchains** in CI/CD for faster builds

7. **Use system toolchains** for quick development iterations

Next Steps
----------

- See :doc:`cli-usage` for using toolchains with CLI
- Learn about :doc:`platforms` for platform-specific toolchain details
- Check :doc:`../getting-started/troubleshooting` for toolchain issues
