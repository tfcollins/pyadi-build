pyadi-build Documentation
=========================

Welcome to the documentation for **pyadi-build**, a Python module for generating and running build commands for Analog Devices, Inc. (ADI) projects including Linux kernel, HDL, and libiio.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Getting Started
      :link: getting-started/index
      :link-type: doc
      :text-align: center

      :octicon:`rocket;2em`

      New to pyadi-build? Start here to install and run your first build.

   .. grid-item-card:: User Guide
      :link: user-guide/index
      :link-type: doc
      :text-align: center

      :octicon:`book;2em`

      Learn how to use the CLI and Python API to build kernels and manage toolchains.

   .. grid-item-card:: API Reference
      :link: api-reference/index
      :link-type: doc
      :text-align: center

      :octicon:`code;2em`

      Complete Python API documentation for using pyadi-build as a library.

   .. grid-item-card:: MCP Server
      :link: mcp-server/index
      :link-type: doc
      :text-align: center

      :octicon:`server;2em`

      Use pyadi-build with AI assistants like Claude via the Model Context Protocol.

   .. grid-item-card:: Developer Guide
      :link: developer-guide/index
      :link-type: doc
      :text-align: center

      :octicon:`tools;2em`

      Contribute to pyadi-build, add new platforms, or extend functionality.

Features
--------

- **Linux Kernel Builder**: Build ADI Linux kernels for Zynq, ZynqMP, and MicroBlaze platforms
- **Automatic Toolchain Management**: Auto-detect or download cross-compilation toolchains
- **Configuration Management**: YAML-based configuration with schema validation
- **Multiple Platform Support**: Zynq (ARM32), ZynqMP (ARM64), and MicroBlaze (soft-core) platforms
- **Device Tree Support**: Build and package device tree blobs (DTBs)
- **Rich CLI**: Beautiful command-line interface with progress indicators
- **Python API**: Use as a library in your own Python scripts
- **MCP Server**: Integration with Model Context Protocol for AI assistants

Quick Examples
--------------

Command Line
~~~~~~~~~~~~

Build a ZynqMP kernel:

.. code-block:: bash

   adibuild linux build -p zynqmp -t 2023_R2

Build with custom configuration:

.. code-block:: bash

   adibuild linux build -p zynq -t 2023_R2 --clean -j 16

Check available toolchains:

.. code-block:: bash

   adibuild toolchain

Python API
~~~~~~~~~~

Build a kernel programmatically:

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

Installation
------------

Install from PyPI:

.. code-block:: bash

   pip install pyadi-build

Or install for development:

.. code-block:: bash

   git clone https://github.com/analogdevicesinc/pyadi-build.git
   cd pyadi-build
   pip install -e ".[dev]"

Documentation Sections
----------------------

.. toctree::
   :maxdepth: 2
   :hidden:

   getting-started/index
   user-guide/index
   api-reference/index
   mcp-server/index
   developer-guide/index
   examples/index

.. toctree::
   :maxdepth: 1
   :caption: External Links
   :hidden:

   GitHub Repository <https://github.com/analogdevicesinc/pyadi-build>
   Issue Tracker <https://github.com/analogdevicesinc/pyadi-build/issues>
   ADI GitHub <https://github.com/analogdevicesinc>
   ADI Linux Kernel <https://github.com/analogdevicesinc/linux>

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
