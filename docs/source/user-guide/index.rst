User Guide
==========

Welcome to the pyadi-build user guide. This section provides comprehensive documentation
for using pyadi-build as both a CLI tool and Python library.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: CLI Usage
      :link: cli-usage
      :link-type: doc
      :text-align: center

      :octicon:`terminal;2em`

      Complete command-line interface reference

   .. grid-item-card:: Python API Usage
      :link: python-api-usage
      :link-type: doc
      :text-align: center

      :octicon:`code;2em`

      Using pyadi-build as a Python library

   .. grid-item-card:: Configuration Guide
      :link: configuration-guide
      :link-type: doc
      :text-align: center

      :octicon:`gear;2em`

      Complete YAML configuration reference

   .. grid-item-card:: Toolchain Management
      :link: toolchain-management
      :link-type: doc
      :text-align: center

      :octicon:`package;2em`

      Managing cross-compilation toolchains

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Platform Guide
      :link: platforms
      :link-type: doc
      :text-align: center

      :octicon:`cpu;2em`

      Zynq, ZynqMP, and MicroBlaze platform details

   .. grid-item-card:: Build Outputs
      :link: build-outputs
      :link-type: doc
      :text-align: center

      :octicon:`package-dependents;2em`

      Understanding build artifacts

   .. grid-item-card:: HDL Builds
      :link: hdl-builds
      :link-type: doc
      :text-align: center

      :octicon:`circuit-board;2em`

      Building HDL projects for ADI hardware

   .. grid-item-card:: no-OS Builds
      :link: noos-builds
      :link-type: doc
      :text-align: center

      :octicon:`cpu;2em`

      Building no-OS bare-metal firmware

   .. grid-item-card:: MCP Server
      :link: mcp-server
      :link-type: doc
      :text-align: center

      :octicon:`server;2em`

      Using the Model Context Protocol server

Topics Covered
--------------

**CLI Usage**
   Complete reference for all CLI commands, options, and workflows

**Python API**
   How to use pyadi-build programmatically in your Python scripts

**Configuration**
   Detailed YAML configuration guide with all available options

**Toolchains**
   Understanding the three toolchain types and how they're managed

**Platforms**
   Platform-specific details for Zynq, ZynqMP, and MicroBlaze

**HDL Builds**
   Guide for building HDL projects, including configuration and version management

**MCP Server**
   Guide for using the Model Context Protocol server integration

**Build Outputs**
   Understanding the structure and contents of build artifacts

Who This Guide Is For
----------------------

This guide is for:

- **CLI users** who want to build kernels from the command line
- **Python developers** integrating pyadi-build into scripts or tools
- **System administrators** setting up build environments
- **CI/CD engineers** automating kernel builds

Prerequisites
-------------

Before using this guide, you should have:

- Completed the :doc:`../getting-started/index`
- Basic understanding of Linux kernel builds
- Familiarity with YAML configuration (for advanced topics)
- Python knowledge (for Python API usage)

.. toctree::
   :maxdepth: 2
   :hidden:

   cli-usage
   python-api-usage
   configuration-guide
   toolchain-management
   platforms
   hdl-builds
   noos-builds
   boot-bin-generation
   build-outputs

