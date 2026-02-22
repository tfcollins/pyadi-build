Platforms API
=============

Platform-specific classes.

Modules
-------

.. toctree::
   :maxdepth: 1

   base
   zynq
   zynqmp
   microblaze
   hdl
   noos

Overview
--------

The platforms package contains platform-specific implementations:

- **base** - PlatformBase abstract class
- **zynq** - Zynq (ARM32) platform
- **zynqmp** - ZynqMP (ARM64) platform
- **microblaze** - MicroBlaze (soft-core) platform
- **hdl** - Generic platform wrapper for HDL projects
- **noos** - no-OS bare-metal firmware platform

Quick Example
-------------

.. code-block:: python

   from adibuild import BuildConfig
   from adibuild.platforms import ZynqPlatform, ZynqMPPlatform, MicroBlazePlatform

   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # Zynq platform
   zynq_config = config.get_platform('zynq')
   zynq = ZynqPlatform(zynq_config)

   # ZynqMP platform
   zynqmp_config = config.get_platform('zynqmp')
   zynqmp = ZynqMPPlatform(zynqmp_config)

   # MicroBlaze platform
   microblaze_config = config.get_platform('microblaze_vcu118')
   microblaze = MicroBlazePlatform(microblaze_config)
