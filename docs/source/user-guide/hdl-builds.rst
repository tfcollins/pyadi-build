HDL Builds
==========

This guide explains how to build HDL projects for Analog Devices hardware using ``adibuild``.

Overview
--------

The HDL build process automates the generation of bitstreams (`.bit`) and hardware definition files (`.xsa`) for ADI reference designs. It handles cloning, version checking, and build execution across different operating systems.

.. mermaid::

   flowchart TD
       Start([Start Build]) --> Config{Config Type?}
       Config -->|Platform| LoadConfig[Load Config File]
       Config -->|Args| ParseArgs[Parse CLI Args]
       LoadConfig & ParseArgs --> PrepSource[Clone/Prepare Source]
       PrepSource --> CheckVer{Check Vivado Ver}
       CheckVer -->|Mismatch| Fail[Error]
       CheckVer -->|Match/Ignore| DetectOS{OS?}
       DetectOS -->|Linux| RunMake[Run make]
       DetectOS -->|Windows| RunTcl[Run Vivado Tcl]
       RunMake & RunTcl --> Collect[Collect Artifacts]
       Collect --> End([Done])
       
       style Start fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff
       style End fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff
       style CheckVer fill:#f9f,stroke:#333,stroke-width:2px
       style DetectOS fill:#f9f,stroke:#333,stroke-width:2px

It handles:

1.  Cloning the `hdl` repository.
2.  Checking out the correct release tag.
3.  Verifying the Vivado toolchain version.
4.  Running the build using `make`.
5.  Collecting build artifacts.

Prerequisites
-------------

*   **Xilinx Vivado/Vitis**: Must be installed and available.
*   **Version Match**: The installed Vivado version usually must match the version required by the HDL release (e.g., release `hdl_2023_r2` typically requires Vivado 2023.2).

Basic Usage
-----------

There are two ways to build HDL projects: using a **configuration file** or using **dynamic arguments**.

Method 1: Using Configuration File
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have a platform defined in your configuration file:

.. code-block:: yaml

   # config.yaml
   project: hdl
   repository: https://github.com/analogdevicesinc/hdl.git
   tag: hdl_2023_r2
   platforms:
     zed_fmcomms2:
       hdl_project: fmcomms2
       carrier: zed
       arch: arm

You can build it by referencing the platform name:

.. code-block:: bash

   adibuild hdl build -p zed_fmcomms2

Method 2: Dynamic Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can specify the project and carrier directly on the command line without defining them in the configuration file first. This is useful for one-off builds or scripting.

.. code-block:: bash

   adibuild hdl build --project fmcomms2 --carrier zed

Command Reference
-----------------

.. code-block:: bash

   adibuild hdl build [OPTIONS]

Options
~~~~~~~

.. option:: --platform PLATFORM, -p PLATFORM

   Target platform defined in configuration file (e.g., `zed_fmcomms2`). Mutually exclusive with `--project`/`--carrier`.

.. option:: --project PROJECT

   HDL project name (e.g., `fmcomms2`, `daq2`). Required if `--platform` is not used.

.. option:: --carrier CARRIER

   Carrier board name (e.g., `zed`, `zcu102`). Required if `--platform` is not used.

.. option:: --arch ARCH

   Target architecture (e.g., `arm`, `arm64`). Defaults to `unknown` if not specified. Used for organizing artifacts.

.. option:: --tag TAG, -t TAG

   Git tag or branch to build (e.g., `hdl_2023_r2`, `main`). Overrides configuration.

.. option:: --output DIR, -o DIR

   Output directory for build artifacts.

.. option:: --clean

   Run `make clean` before building.

.. option:: --jobs N, -j N

   Number of parallel jobs (sets `ADI_MAX_OOC_JOBS`).

.. option:: --ignore-version-check

   Force build even if Vivado version does not match the requirement in the HDL source code. Sets `ADI_IGNORE_VERSION_CHECK=1`.

.. option:: --generate-script

   Generate a bash script (e.g., `build_hdl_arm.sh`) instead of executing the build.

Advanced Features
-----------------

Version Checking
~~~~~~~~~~~~~~~~

The builder automatically scans the project source code (specifically `adi_project_xilinx.tcl` or similar) to find the required Vivado version. If your installed version does not match, the build will fail to prevent unexpected errors.

To override this check (e.g., building an older release with a newer Vivado):

.. code-block:: bash

   adibuild hdl build -p zed_fmcomms2 --ignore-version-check

Windows Support
~~~~~~~~~~~~~~~

If running on Windows, `adibuild` automatically detects the environment and switches from `make` to a pure Tcl-based build flow. This involves:

1.  Generating a temporary Tcl script that sources `adi_make.tcl`.
2.  Running `vivado -mode batch -source ...`.

No extra configuration is needed; simply run the same command as on Linux.

Portable Build Scripts
~~~~~~~~~~~~~~~~~~~~~~

You can generate a standalone bash script to run the build later or on a machine without `adibuild` installed (provided dependencies are met):

.. code-block:: bash

   adibuild hdl build --project daq2 --carrier zcu102 --generate-script

This creates a script in your work directory (e.g., `~/.adibuild/work/build_hdl_unknown.sh`).

Output Artifacts
----------------

After a successful build, artifacts are collected in the output directory:

*   **Bitstream**: `*.bit`
*   **Hardware Handoff**: `*.xsa`

Example output structure:

.. code-block:: text

   hdl-hdl_2023_r2-zed_fmcomms2/
   ├── system_top.bit
   └── system_top.xsa

Remote SSH Builds
-----------------

For HDL builds, you can leverage remote SSH targets that have Vivado installed. This is especially useful
if you don't have Vivado locally or want to distribute builds across multiple machines.

Setup
~~~~~

**1. Add an SSH target with Vivado installed:**

.. code-block:: bash

   adibuild ssh add hdl-dev-2 hdl-dev-2 builder --key-file ~/.ssh/id_rsa

**2. Verify Vivado is available on the target:**

.. code-block:: bash

   adibuild ssh test hdl-dev-2

**3. Select the target for HDL builds:**

.. code-block:: bash

   adibuild ssh select hdl-dev-2

Building on Remote
~~~~~~~~~~~~~~~~~~

Once configured, run HDL builds normally - they'll execute remotely:

.. code-block:: bash

   # Uses selected target (hdl-dev-2)
   adibuild hdl build -p zed_fmcomms2

   # Or override target for this build only
   adibuild hdl build -p zed_fmcomms2 --remote-target hdl-dev-2

Configuration
~~~~~~~~~~~~~

Add SSH targets to your config file:

.. code-block:: yaml

   ssh_targets:
     hdl-dev-2:
       hostname: hdl-dev-2
       username: builder
       key_file: ~/.ssh/id_rsa
       work_dir: ~/.adibuild/work

   build:
     selected_target: hdl-dev-2

   platforms:
     zed_fmcomms2:
       hdl_project: fmcomms2
       carrier: zed
       arch: arm

Example Workflow with Real Integration Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To verify Vivado compatibility on a target like ``hdl-dev-2``, run:

.. code-block:: bash

   # Run SSH integration tests against hdl-dev-2
   pytest --real-ssh --ssh-target hdl-dev-2 test/integration/test_ssh_hdl_build.py -v

These tests verify:

- SSH connectivity to the target
- Vivado availability
- Required build tools (make, git, bash)
- Remote directory creation
- Environment variable passing
- HDL source access

For more SSH configuration details, see :doc:`cli-usage` and :doc:`configuration-guide`.
