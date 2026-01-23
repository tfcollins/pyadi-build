BuildConfig
===========

Configuration management for pyadi-build.

.. currentmodule:: adibuild.core.config

.. autoclass:: BuildConfig
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Class Methods

   .. automethod:: from_yaml
   .. automethod:: from_dict

   .. rubric:: Instance Methods

   .. automethod:: get
   .. automethod:: set
   .. automethod:: get_platform
   .. automethod:: to_dict

   .. rubric:: Example Usage

   **Loading Configuration:**

   .. code-block:: python

      from adibuild import BuildConfig

      # From YAML file
      config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

      # From dictionary
      config_dict = {
          'project': 'linux',
          'repository': 'https://github.com/analogdevicesinc/linux.git',
          'tag': '2023_R2',
          'platforms': {
              'zynqmp': {
                  'arch': 'arm64',
                  'cross_compile': 'aarch64-linux-gnu-',
                  'defconfig': 'adi_zynqmp_defconfig',
                  'kernel_target': 'Image',
              }
          }
      }
      config = BuildConfig(config_dict)

   **Accessing Configuration:**

   .. code-block:: python

      # Get values
      project = config.get('project')
      repository = config.get('repository')
      tag = config.get('tag')

      # Get nested values
      parallel_jobs = config.get('build.parallel_jobs', default=8)

      # Get platform configuration
      platform_config = config.get_platform('zynqmp')
      arch = platform_config['arch']

   **Modifying Configuration:**

   .. code-block:: python

      # Set values
      config.set('tag', 'main')
      config.set('build.parallel_jobs', 16)
      config.set('build.output_dir', '/tmp/build')

      # Modify platform configuration
      platform_config = config.get_platform('zynqmp')
      platform_config['defconfig'] = 'my_custom_defconfig'
      config.set('platforms.zynqmp', platform_config)

   **Converting to Dictionary:**

   .. code-block:: python

      # Get full configuration as dictionary
      config_dict = config.to_dict()
      import json
      print(json.dumps(config_dict, indent=2))

See Also
--------

- :doc:`../../../user-guide/configuration-guide` - Configuration file format
- :doc:`../../../getting-started/configuration-basics` - Basic configuration concepts
