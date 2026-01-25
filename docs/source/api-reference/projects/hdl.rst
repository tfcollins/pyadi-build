HDLBuilder
==========

HDL project builder.

.. currentmodule:: adibuild.projects.hdl

.. autoclass:: HDLBuilder
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: build
   .. automethod:: prepare_source
   .. automethod:: clean
   .. automethod:: package_artifacts

   .. rubric:: Example Usage

   **Basic Build:**

   .. code-block:: python

      from adibuild import HDLBuilder, BuildConfig
      from adibuild.platforms.hdl import HDLPlatform

      config = BuildConfig.from_yaml('config.yaml')
      platform_config = config.get_platform('zed_fmcomms2')
      # HDLPlatform requires config dict, name is usually injected
      platform_config['name'] = 'zed_fmcomms2'
      platform = HDLPlatform(platform_config)

      builder = HDLBuilder(config, platform)
      result = builder.build()

      print(f"Build completed in {result.get('duration', 0):.1f}s")
      print(f"Artifacts: {result['artifacts']}")

   **Clean Build:**

   .. code-block:: python

      builder = HDLBuilder(config, platform)
      builder.clean(deep=False)
      builder.build()

Build Result
------------

The ``build()`` method returns a dictionary with:

.. code-block:: python

   {
       'artifacts': {
           'xsa': ['/path/to/system_top.xsa'],
           'bit': ['/path/to/system_top.bit']
       },
       'output_dir': '/path/to/build/hdl-tag-platform'
   }

See Also
--------

- :doc:`../core/builder` - BuilderBase class
- :doc:`../platforms/index` - Platform classes
