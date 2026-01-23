Validators
==========

Configuration validation utilities.

.. currentmodule:: adibuild.utils.validators

.. autofunction:: validate_config

.. autofunction:: validate_platform_config

Example Usage
-------------

**Validate Configuration:**

.. code-block:: python

   from adibuild.utils.validators import validate_config
   from pathlib import Path

   config_path = Path('my_config.yaml')
   schema_path = Path('configs/schema/linux_config.schema.json')

   try:
       validate_config(config_path, schema_path)
       print("Configuration is valid!")
   except ValueError as e:
       print(f"Validation error: {e}")

**Validate Platform Configuration:**

.. code-block:: python

   from adibuild.utils.validators import validate_platform_config

   platform_config = {
       'arch': 'arm64',
       'cross_compile': 'aarch64-linux-gnu-',
       'defconfig': 'adi_zynqmp_defconfig',
       'kernel_target': 'Image',
       'dtb_path': 'arch/arm64/boot/dts/xilinx',
       'kernel_image_path': 'arch/arm64/boot/Image',
   }

   try:
       validate_platform_config(platform_config, 'zynqmp')
       print("Platform configuration is valid!")
   except ValueError as e:
       print(f"Platform validation error: {e}")

See Also
--------

- :doc:`../core/config` - BuildConfig class
- :doc:`../../user-guide/configuration-guide` - Configuration guide
