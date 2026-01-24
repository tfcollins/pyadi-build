MicroBlazePlatform
==================

MicroBlaze (soft-core) platform support for Xilinx Virtex FPGAs.

.. currentmodule:: adibuild.platforms.microblaze

.. autoclass:: MicroBlazePlatform
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild import BuildConfig
      from adibuild.platforms import MicroBlazePlatform

      config = BuildConfig.from_yaml('configs/linux/microblaze_vcu118_ad9081.yaml')
      platform_config = config.get_platform('microblaze_vcu118')
      platform = MicroBlazePlatform(platform_config)

      print(f"Architecture: {platform.arch}")              # microblaze
      print(f"Defconfig: {platform.defconfig}")            # adi_mb_defconfig
      print(f"Kernel target: {platform.kernel_target}")    # simpleImage.vcu118_ad9081
      print(f"Targets: {platform.simpleimage_targets}")    # List of simpleImage targets

      # Get toolchain (Vivado required)
      toolchain = platform.get_toolchain()
      print(f"Toolchain: {toolchain.type}")
      print(f"Cross-compile: {toolchain.cross_compile_microblaze}")

Platform Configuration
----------------------

Required configuration fields:

.. code-block:: yaml

   platforms:
     microblaze_vcu118:
       arch: microblaze
       cross_compile: microblazeel-xilinx-linux-gnu-
       defconfig: adi_mb_defconfig
       kernel_target: simpleImage.vcu118_ad9081
       dtb_path: arch/microblaze/boot/dts
       kernel_image_path: arch/microblaze/boot/simpleImage.vcu118_ad9081

       simpleimage_targets:
         - simpleImage.vcu118_ad9081

       dtbs: []

       toolchain:
         preferred: vivado
         fallback: []

simpleImage Targets
-------------------

The ``simpleimage_targets`` property allows building multiple kernel images
with different device trees in a single build:

.. code-block:: yaml

   simpleimage_targets:
     - simpleImage.vcu118_ad9081
     - simpleImage.vcu118_ad9082

Each target produces a separate ``simpleImage.<name>`` file.

See Also
--------

- :doc:`base` - PlatformBase class
- :doc:`../../user-guide/platforms` - Platform guide
- :doc:`../projects/linux` - LinuxBuilder usage
- `ADI MicroBlaze Documentation <https://analogdevicesinc.github.io/documentation/linux/kernel/microblaze.html>`_
