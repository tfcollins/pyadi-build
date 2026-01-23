LinuxBuilder
============

Linux kernel builder.

.. currentmodule:: adibuild.projects.linux

.. autoclass:: LinuxBuilder
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: build
   .. automethod:: prepare_source
   .. automethod:: configure
   .. automethod:: menuconfig
   .. automethod:: build_kernel
   .. automethod:: build_dtbs
   .. automethod:: clean
   .. automethod:: package_artifacts

   .. rubric:: Example Usage

   **Basic Build:**

   .. code-block:: python

      from adibuild import LinuxBuilder, BuildConfig
      from adibuild.platforms import ZynqMPPlatform

      config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
      platform_config = config.get_platform('zynqmp')
      platform = ZynqMPPlatform(platform_config)

      builder = LinuxBuilder(config, platform)
      result = builder.build()

      print(f"Build completed in {result['duration']:.1f}s")
      print(f"Artifacts: {result['artifacts']}")

   **Step-by-Step Build:**

   .. code-block:: python

      builder = LinuxBuilder(config, platform)

      # Prepare source
      builder.prepare_source()

      # Configure kernel
      builder.configure()

      # Build kernel image
      kernel_image = builder.build_kernel()
      print(f"Kernel: {kernel_image}")

      # Build device trees
      dtbs = builder.build_dtbs()
      print(f"DTBs: {dtbs}")

      # Package artifacts
      output_dir = builder.package_artifacts(kernel_image, dtbs)
      print(f"Output: {output_dir}")

   **Custom Configuration:**

   .. code-block:: python

      builder = LinuxBuilder(config, platform)

      # Prepare and configure
      builder.prepare_source()
      builder.configure()

      # Run menuconfig
      builder.menuconfig()

      # Build with custom config
      kernel_image = builder.build_kernel()
      dtbs = builder.build_dtbs()
      output_dir = builder.package_artifacts(kernel_image, dtbs)

   **Clean Build:**

   .. code-block:: python

      builder = LinuxBuilder(config, platform)

      # Clean build artifacts
      builder.prepare_source()
      builder.clean(deep=False)

      # Or deep clean (mrproper)
      builder.clean(deep=True)

      # Build
      result = builder.build()

   **Build Only DTBs:**

   .. code-block:: python

      builder = LinuxBuilder(config, platform)

      # Build only device trees
      result = builder.build(dtbs_only=True)

      # Or build specific DTBs
      builder.prepare_source()
      builder.configure()
      dtbs = builder.build_dtbs(dtbs=[
          'zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb',
      ])

Build Result
------------

The ``build()`` method returns a dictionary with:

.. code-block:: python

   {
       'success': True,
       'duration': 847.3,
       'kernel_image': 'Image',
       'dtbs': ['zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb', ...],
       'artifacts': Path('/path/to/build/linux-2023_R2-arm64'),
       'metadata': {
           'project': 'linux',
           'platform': 'zynqmp',
           'architecture': 'arm64',
           'tag': '2023_R2',
           'commit': 'a1b2c3d...',
           'build_date': '2024-01-23T10:15:30',
           'toolchain': {...}
       }
   }

See Also
--------

- :doc:`../core/builder` - BuilderBase class
- :doc:`../platforms/index` - Platform classes
- :doc:`../../user-guide/python-api-usage` - Python API guide
