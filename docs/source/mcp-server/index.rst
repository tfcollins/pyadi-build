MCP Server
==========

pyadi-build includes a built-in `Model Context Protocol (MCP) <https://modelcontextprotocol.io/>`_ server. This allows AI assistants and Large Language Models (LLMs) to directly interact with the build system to explore, configure, and build projects in a safe and structured way.

Installation
------------

The MCP server requires additional dependencies. Install pyadi-build with the ``mcp`` extra:

.. code-block:: bash

   pip install "pyadi-build[mcp]"

Or for development:

.. code-block:: bash

   pip install -e ".[mcp]"

Usage
-----

Start the MCP server using the CLI:

.. code-block:: bash

   adibuild mcp

This will start the server on stdio, which is the standard transport for local MCP clients.

Client Configuration
--------------------

Claude Desktop
~~~~~~~~~~~~~~

To use pyadi-build with `Claude Desktop <https://claude.ai/download>`_, add the following to your configuration file (typically ``~/Library/Application Support/Claude/claude_desktop_config.json`` on macOS or ``%APPDATA%\\Claude\\claude_desktop_config.json`` on Windows):

.. code-block:: json

   {
     "mcpServers": {
       "pyadi-build": {
         "command": "adibuild",
         "args": ["mcp"]
       }
     }
   }

API Reference
-------------

The server exposes the following tools to connected clients.

Platform & Toolchain Discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. function:: list_platforms(config_path: str = None) -> list[str]

   List available platforms from the configuration.

   :param config_path: Path to configuration file (optional)
   :return: List of platform names

.. function:: list_toolchains(platform: str = None) -> dict

   Detect and display available toolchains (Vivado/Vitis, ARM GNU, System).

   :param platform: Optional platform name to show which toolchain would be selected for it.
   :return: Dictionary containing detected toolchains and selection details.

.. function:: get_version() -> str

   Return the current version of pyadi-build.

   :return: Version string

Linux Kernel Operations
~~~~~~~~~~~~~~~~~~~~~~~

.. function:: build_linux_platform(platform: str, tag: str = None, config_path: str = None, clean: bool = False, defconfig: str = None, output: str = None, dtbs_only: bool = False, jobs: int = None, generate_script: bool = False, simpleimage_targets: list[str] = None, tool_version: str = None, allow_any_vivado: bool = False) -> str

   Build Linux kernel for a specific platform.

   :param platform: Target platform (e.g., zynq, zynqmp, microblaze)
   :param tag: Git tag or branch to build (e.g., 2023_R2)
   :param config_path: Path to configuration file
   :param clean: Whether to clean before building
   :param defconfig: Override defconfig
   :param output: Output directory
   :param dtbs_only: Build only device tree blobs
   :param jobs: Number of parallel jobs
   :param generate_script: Generate bash script instead of executing build
   :param simpleimage_targets: List of simpleImage targets (MicroBlaze only)
   :param tool_version: Override toolchain version (e.g., 2023.2)
   :param allow_any_vivado: Allow any Vivado version instead of requiring exact match
   :return: Build result summary

.. function:: configure_linux_platform(platform: str, tag: str = None, config_path: str = None, defconfig: str = None) -> str

   Configure kernel without building. Useful for preparing the source tree for manual inspection or menuconfig.

   :param platform: Target platform
   :param tag: Git tag or branch
   :param config_path: Configuration file path
   :param defconfig: Override defconfig
   :return: Status message

.. function:: build_linux_dtbs(platform: str, dtb_files: list[str] = None, tag: str = None, config_path: str = None) -> str

   Build specific device tree blobs.

   :param platform: Target platform
   :param dtb_files: List of specific DTB files to build (optional, builds all if empty)
   :param tag: Git tag or branch
   :param config_path: Configuration file path
   :return: Status message

.. function:: clean_linux_platform(platform: str, tag: str = None, config_path: str = None, deep: bool = False) -> str

   Clean kernel build artifacts.

   :param platform: Target platform
   :param tag: Git tag or branch
   :param config_path: Configuration file path
   :param deep: If True, uses mrproper (removes config). If False, uses distclean.
   :return: Status message

HDL Project Operations
~~~~~~~~~~~~~~~~~~~~~~

.. function:: build_hdl_project(project: str = None, carrier: str = None, platform: str = None, arch: str = "unknown", tag: str = None, output: str = None, clean: bool = False, jobs: int = None, ignore_version_check: bool = False, generate_script: bool = False, tool_version: str = None) -> str

   Build an HDL project.

   :param project: HDL project name (e.g. fmcomms2). Required if platform not set.
   :param carrier: Carrier board name (e.g. zed). Required if platform not set.
   :param platform: Target platform/build config (e.g. zed_fmcomms2). Alternative to project/carrier.
   :param arch: Architecture (e.g. arm, arm64)
   :param tag: Git tag or branch to build
   :param output: Output directory
   :param clean: Whether to clean before building
   :param jobs: Number of parallel jobs
   :param ignore_version_check: Ignore Vivado version check
   :param generate_script: Generate bash script instead of executing build
   :param tool_version: Override Vivado version
   :return: Build result summary

Utilities
~~~~~~~~~

.. function:: list_simpleimage_presets(tag: str, carrier: str = None) -> list[dict]

   List available simpleImage presets for a given release tag (MicroBlaze).

   :param tag: Release tag (e.g., 2023_R2)
   :param carrier: Optional carrier filter (e.g., vcu118)
   :return: List of presets

.. function:: validate_configuration(config_file: str) -> str

   Validate configuration file against schema.

   :param config_file: Path to configuration file
   :return: Validation result message
