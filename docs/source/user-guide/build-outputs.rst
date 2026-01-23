Build Outputs
=============

This guide explains the structure and contents of pyadi-build output artifacts.

Output Directory Structure
---------------------------

After a successful build, artifacts are organized in this structure:

.. code-block:: text

   build/
   └── linux-{tag}-{arch}/
       ├── Image or uImage      # Kernel image
       ├── dts/                 # Device tree blobs
       │   ├── board1.dtb
       │   ├── board2.dtb
       │   └── ...
       └── metadata.json        # Build metadata

**Directory Naming:**

- ``{tag}``: Git tag or branch name (e.g., ``2023_R2``, ``main``)
- ``{arch}``: Architecture (``arm`` for Zynq, ``arm64`` for ZynqMP)

**Examples:**

.. code-block:: text

   build/linux-2023_R2-arm64/     # ZynqMP build
   build/linux-2023_R2-arm/       # Zynq build
   build/linux-main-arm64/        # ZynqMP from main branch

Kernel Image
------------

Zynq (uImage)
~~~~~~~~~~~~~

**File:** ``uImage``

**Format:** U-Boot wrapped kernel image

**Size:** ~3-5 MB (compressed)

**Structure:**

.. code-block:: text

   +-----------------+
   | U-Boot Header   |  64 bytes
   |   - Magic       |
   |   - Load Addr   |
   |   - Entry Point |
   |   - Size        |
   |   - CRC         |
   +-----------------+
   | Compressed      |  ~3-5 MB
   | Kernel Image    |
   | (zImage)        |
   +-----------------+

**Usage:**

Load with U-Boot:

.. code-block:: text

   U-Boot> tftp 0x8000000 uImage
   U-Boot> tftp 0x2000000 devicetree.dtb
   U-Boot> bootm 0x8000000 - 0x2000000

Inspect header:

.. code-block:: bash

   mkimage -l uImage

**Output:**

.. code-block:: text

   Image Name:   Linux-5.15.0
   Created:      Wed Jan 23 10:15:30 2024
   Image Type:   ARM Linux Kernel Image (uncompressed)
   Data Size:    4123456 Bytes = 4027.78 KiB = 3.93 MiB
   Load Address: 00008000
   Entry Point:  00008000

ZynqMP (Image)
~~~~~~~~~~~~~~

**File:** ``Image``

**Format:** Raw ARM64 kernel binary

**Size:** ~18-22 MB (uncompressed)

**Structure:**

.. code-block:: text

   +-----------------+
   | ARM64 Header    |  64 bytes
   |   - Magic       |
   |   - Text Offset |
   |   - Image Size  |
   |   - Flags       |
   +-----------------+
   | Kernel Code     |  ~18-22 MB
   | and Data        |
   +-----------------+

**Usage:**

Load with U-Boot:

.. code-block:: text

   U-Boot> tftp 0x8000000 Image
   U-Boot> tftp 0x2000000 devicetree.dtb
   U-Boot> booti 0x8000000 - 0x2000000

Check image:

.. code-block:: bash

   file Image

**Output:**

.. code-block:: text

   Image: Linux kernel ARM64 boot executable Image, little-endian, 4K pages

Device Tree Blobs
-----------------

Location
~~~~~~~~

DTBs are stored in the ``dts/`` subdirectory:

.. code-block:: text

   build/linux-2023_R2-arm64/dts/
   ├── zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   ├── zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
   ├── zynqmp-zcu102-rev10-adrv9009-fmcomms8.dtb
   └── ...

Format
~~~~~~

Device tree blobs are compiled binary representations of hardware descriptions.

**Size:** ~30-60 KB per DTB

**Structure:**

.. code-block:: text

   +-----------------+
   | DTB Header      |
   |   - Magic       |  0xd00dfeed
   |   - Total Size  |
   |   - Struct Offs |
   |   - Strings Offs|
   +-----------------+
   | Memory Rsv Map  |
   +-----------------+
   | Structure Block |  Hardware description
   +-----------------+
   | Strings Block   |  String table
   +-----------------+

Inspecting DTBs
~~~~~~~~~~~~~~~

Decompile to source:

.. code-block:: bash

   dtc -I dtb -O dts zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb -o device-tree.dts

Check DTB info:

.. code-block:: bash

   fdtdump zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb

Usage
~~~~~

Load with kernel:

.. code-block:: text

   U-Boot> tftp 0x8000000 Image
   U-Boot> tftp 0x2000000 zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
   U-Boot> booti 0x8000000 - 0x2000000

Metadata File
-------------

The ``metadata.json`` file contains build information for traceability.

Structure
~~~~~~~~~

.. code-block:: json

   {
     "project": "linux",
     "platform": "zynqmp",
     "architecture": "arm64",
     "tag": "2023_R2",
     "commit": "a1b2c3d4e5f6789...",
     "build_date": "2024-01-23T10:15:30.123456",
     "duration": 847.3,
     "toolchain": {
       "type": "vivado",
       "version": "12.2.0",
       "cross_compile": "aarch64-xilinx-linux-gnu-",
       "path": "/opt/Xilinx/Vitis/2023.2/aarch64-xilinx-linux"
     },
     "artifacts": {
       "kernel_image": "Image",
       "kernel_size": 19456789,
       "dtbs": [
         "dts/zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb",
         "dts/zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb"
       ],
       "dtb_count": 2
     },
     "configuration": {
       "defconfig": "adi_zynqmp_defconfig",
       "parallel_jobs": 8
     }
   }

Fields
~~~~~~

.. describe:: project

   Project type (``linux``)

.. describe:: platform

   Platform name (``zynq`` or ``zynqmp``)

.. describe:: architecture

   Target architecture (``arm`` or ``arm64``)

.. describe:: tag

   Git tag or branch that was built

.. describe:: commit

   Full git commit SHA

.. describe:: build_date

   ISO 8601 timestamp of build

.. describe:: duration

   Build duration in seconds

.. describe:: toolchain.type

   Toolchain type used (``vivado``, ``arm``, or ``system``)

.. describe:: toolchain.version

   GCC version

.. describe:: toolchain.cross_compile

   Cross-compiler prefix

.. describe:: artifacts.kernel_image

   Kernel image filename

.. describe:: artifacts.kernel_size

   Kernel image size in bytes

.. describe:: artifacts.dtbs

   List of built DTB files

Reading Metadata
~~~~~~~~~~~~~~~~

**Python:**

.. code-block:: python

   import json
   from pathlib import Path

   metadata_path = Path('build/linux-2023_R2-arm64/metadata.json')
   with open(metadata_path) as f:
       metadata = json.load(f)

   print(f"Built commit: {metadata['commit']}")
   print(f"Build time: {metadata['duration']:.1f}s")
   print(f"Toolchain: {metadata['toolchain']['version']}")

**Bash:**

.. code-block:: bash

   jq '.' build/linux-2023_R2-arm64/metadata.json

   # Extract specific fields
   jq '.commit' build/linux-2023_R2-arm64/metadata.json
   jq '.toolchain.version' build/linux-2023_R2-arm64/metadata.json

Build Artifacts Size
--------------------

Typical Sizes
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 30 20 20 30

   * - Component
     - Zynq
     - ZynqMP
     - Notes
   * - Kernel Image
     - 3-5 MB
     - 18-22 MB
     - Compressed vs uncompressed
   * - Single DTB
     - 30-50 KB
     - 40-60 KB
     - Varies by hardware
   * - All DTBs
     - 200-300 KB
     - 300-500 KB
     - 6-8 DTBs typically
   * - Total
     - 3-6 MB
     - 19-23 MB
     - Image + DTBs

Disk Space
~~~~~~~~~~

**Working Space:**

- Kernel source: ~4 GB
- Build objects: ~5-6 GB
- **Total:** ~10 GB

**Output Artifacts:**

- Build directory: ~20-25 MB per platform

**Toolchain Cache:**

- ARM GNU toolchain: ~120 MB per architecture
- Total for both ARM32/ARM64: ~240 MB

Artifact Verification
---------------------

Checksums
~~~~~~~~~

Generate checksums for artifacts:

.. code-block:: bash

   cd build/linux-2023_R2-arm64
   sha256sum Image > checksums.txt
   sha256sum dts/*.dtb >> checksums.txt

Verify:

.. code-block:: bash

   sha256sum -c checksums.txt

File Integrity
~~~~~~~~~~~~~~

Check kernel image:

.. code-block:: bash

   # Zynq
   mkimage -l uImage

   # ZynqMP
   file Image

Check DTBs:

.. code-block:: bash

   for dtb in dts/*.dtb; do
       fdtdump "$dtb" > /dev/null && echo "$dtb: OK" || echo "$dtb: FAILED"
   done

Packaging Artifacts
-------------------

Creating Archive
~~~~~~~~~~~~~~~~

Create tarball of build artifacts:

.. code-block:: bash

   cd build
   tar czf linux-2023_R2-arm64.tar.gz linux-2023_R2-arm64/

With checksums:

.. code-block:: bash

   cd linux-2023_R2-arm64
   sha256sum * dts/* > checksums.txt
   cd ..
   tar czf linux-2023_R2-arm64.tar.gz linux-2023_R2-arm64/

Extracting Archive
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   tar xzf linux-2023_R2-arm64.tar.gz
   cd linux-2023_R2-arm64
   sha256sum -c checksums.txt

Deployment
----------

Copying to SD Card
~~~~~~~~~~~~~~~~~~

For SD card boot:

.. code-block:: bash

   # Mount SD card boot partition
   sudo mount /dev/sdX1 /mnt

   # Copy artifacts
   sudo cp build/linux-2023_R2-arm64/Image /mnt/
   sudo cp build/linux-2023_R2-arm64/dts/zynqmp-zcu102-*.dtb /mnt/

   # Sync and unmount
   sudo sync
   sudo umount /mnt

TFTP Deployment
~~~~~~~~~~~~~~~

For network boot:

.. code-block:: bash

   # Copy to TFTP directory
   sudo cp build/linux-2023_R2-arm64/Image /var/lib/tftpboot/
   sudo cp build/linux-2023_R2-arm64/dts/*.dtb /var/lib/tftpboot/

Programmatic Access
-------------------

Python API
~~~~~~~~~~

Access build artifacts:

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqMPPlatform
   from pathlib import Path
   import json

   # Build
   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)
   builder = LinuxBuilder(config, platform)
   result = builder.build()

   # Access artifacts
   artifacts_dir = result['artifacts']
   kernel_image = artifacts_dir / 'Image'
   dtb_dir = artifacts_dir / 'dts'

   # Read metadata
   metadata_file = artifacts_dir / 'metadata.json'
   with open(metadata_file) as f:
       metadata = json.load(f)

   print(f"Kernel: {kernel_image} ({kernel_image.stat().st_size} bytes)")
   print(f"DTBs: {list(dtb_dir.glob('*.dtb'))}")
   print(f"Commit: {metadata['commit']}")

Cleaning Up
-----------

Remove Build Artifacts
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Remove specific build
   rm -rf build/linux-2023_R2-arm64

   # Remove all builds
   rm -rf build/*

Clean Working Directory
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Clean kernel build objects
   adibuild linux clean -p zynqmp -t 2023_R2 --deep

   # Remove entire working directory
   rm -rf ~/.adibuild/work

Best Practices
--------------

1. **Verify artifacts** after build using checksums

2. **Archive builds** with metadata for traceability

3. **Version artifacts** - include git commit in filenames

4. **Test on hardware** before deploying to production

5. **Keep metadata** - maintain build information for debugging

6. **Automate packaging** in CI/CD pipelines

7. **Use TFTP for development** - faster iteration than SD cards

8. **Keep SD card backups** - working images for recovery

Next Steps
----------

- Learn about :doc:`platforms` for platform-specific artifacts
- See :doc:`../examples/advanced/index` for CI/CD packaging examples
- Check :doc:`../getting-started/troubleshooting` if artifacts are missing
