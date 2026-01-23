ZynqPlatform
============

Zynq (ARM32) platform support.

.. currentmodule:: adibuild.platforms.zynq

.. autoclass:: ZynqPlatform
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild import BuildConfig
      from adibuild.platforms import ZynqPlatform

      config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
      platform_config = config.get_platform('zynq')
      platform = ZynqPlatform(platform_config)

      print(f"Architecture: {platform.arch}")         # arm
      print(f"Defconfig: {platform.defconfig}")       # zynq_xcomm_adv7511_defconfig
      print(f"Kernel target: {platform.kernel_target}") # uImage

      # Get toolchain
      toolchain = platform.get_toolchain()
      print(f"Toolchain: {toolchain['type']}")
      print(f"Cross-compile: {toolchain['cross_compile']}")

Platform Configuration
----------------------

Required configuration fields:

.. code-block:: yaml

   platforms:
     zynq:
       arch: arm
       cross_compile: arm-linux-gnueabihf-
       defconfig: zynq_xcomm_adv7511_defconfig
       kernel_target: uImage
       dtb_path: arch/arm/boot/dts
       kernel_image_path: arch/arm/boot/uImage

       dtbs:
         - zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
         - zynq-zc706-adv7511-ad9361-fmcomms2-3.dtb

       toolchain:
         preferred: vivado
         fallback:
           - arm
           - system

See Also
--------

- :doc:`base` - PlatformBase class
- :doc:`../../user-guide/platforms` - Platform guide
- :doc:`../projects/linux` - LinuxBuilder usage
