ZynqMPPlatform
==============

ZynqMP (ARM64) platform support.

.. currentmodule:: adibuild.platforms.zynqmp

.. autoclass:: ZynqMPPlatform
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild import BuildConfig
      from adibuild.platforms import ZynqMPPlatform

      config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
      platform_config = config.get_platform('zynqmp')
      platform = ZynqMPPlatform(platform_config)

      print(f"Architecture: {platform.arch}")         # arm64
      print(f"Defconfig: {platform.defconfig}")       # adi_zynqmp_defconfig
      print(f"Kernel target: {platform.kernel_target}") # Image

      # Get toolchain
      toolchain = platform.get_toolchain()
      print(f"Toolchain: {toolchain['type']}")
      print(f"Cross-compile: {toolchain['cross_compile']}")

Platform Configuration
----------------------

Required configuration fields:

.. code-block:: yaml

   platforms:
     zynqmp:
       arch: arm64
       cross_compile: aarch64-linux-gnu-
       defconfig: adi_zynqmp_defconfig
       kernel_target: Image
       dtb_path: arch/arm64/boot/dts/xilinx
       kernel_image_path: arch/arm64/boot/Image

       dtbs:
         - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
         - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb

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
