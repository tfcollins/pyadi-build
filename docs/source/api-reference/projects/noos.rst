NoOSBuilder
===========

no-OS bare-metal firmware builder.

.. currentmodule:: adibuild.projects.noos

.. autoclass:: NoOSBuilder
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: build
   .. automethod:: prepare_source
   .. automethod:: configure
   .. automethod:: clean
   .. automethod:: package_artifacts
   .. automethod:: get_output_dir

   .. rubric:: Example Usage

   **Basic Xilinx Build:**

   .. code-block:: python

      from adibuild.core.config import BuildConfig
      from adibuild.platforms.noos import NoOSPlatform
      from adibuild.projects.noos import NoOSBuilder

      config = BuildConfig.from_yaml("noos.yaml")
      platform_config = config.get_platform("xilinx_ad9081")
      platform_config["name"] = "xilinx_ad9081"

      platform = NoOSPlatform(platform_config)
      builder = NoOSBuilder(config, platform)

      result = builder.build()
      print(f"Artifacts: {result['artifacts']['elf']}")

   **Script Generation:**

   .. code-block:: python

      builder = NoOSBuilder(config, platform, script_mode=True)
      builder.build()
      # Generates ~/.adibuild/work/build_noos_bare_metal.sh

   **Clean Build:**

   .. code-block:: python

      builder = NoOSBuilder(config, platform)
      builder.clean(deep=False)   # make clean
      builder.build()

   **Deep Clean:**

   .. code-block:: python

      builder.clean(deep=True)    # make reset

Build Result
------------

The ``build()`` method returns a dictionary with:

.. code-block:: python

   {
       "artifacts": {
           "elf": ["/path/to/build/firmware.elf"],
           "axf": [],
       },
       "output_dir": "/path/to/build/noos-ad9081_fmca_ebz-2023_R2-xilinx",
   }

Output Directory
----------------

Artifacts are placed in:

.. code-block:: text

   <build.output_dir>/noos-<noos_project>-<tag>-<noos_platform>/

Make Invocation
---------------

The builder calls make with the following form:

.. code-block:: bash

   make -j<jobs> -C projects/<noos_project> \
       PLATFORM=<noos_platform> \
       NO-OS=<repo_root> \
       [PROFILE=<profile>] \
       IIOD=y|n \
       [EXTRA_VAR=value ...]

See Also
--------

- :doc:`../platforms/noos` - NoOSPlatform class
- :doc:`../core/builder` - BuilderBase abstract class
- :doc:`../../user-guide/noos-builds` - User guide for no-OS builds
