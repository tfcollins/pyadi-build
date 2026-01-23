Core API
========

Core functionality for configuration, building, execution, and toolchain management.

Modules
-------

.. toctree::
   :maxdepth: 1

   config
   builder
   executor
   toolchain

Overview
--------

The core package provides the fundamental building blocks:

- **config** - Configuration management with BuildConfig class
- **builder** - Abstract builder base class
- **executor** - Command execution and build orchestration
- **toolchain** - Toolchain detection and management

Quick Example
-------------

.. code-block:: python

   from adibuild import BuildConfig, LinuxBuilder
   from adibuild.platforms import ZynqMPPlatform

   # Load configuration
   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # Get platform
   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)

   # Create builder
   builder = LinuxBuilder(config, platform)

   # Execute build
   result = builder.build()
