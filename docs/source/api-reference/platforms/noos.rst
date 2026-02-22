NoOSPlatform
============

Platform configuration for no-OS bare-metal firmware projects.

.. currentmodule:: adibuild.platforms.noos

.. autodata:: VALID_NOOS_PLATFORMS
   :annotation: = ["xilinx", "stm32", "linux", "altera", "aducm3029", "maxim", "pico"]

.. autodata:: NOOS_PLATFORM_TOOLCHAIN
   :annotation: = {platform: preferred_toolchain_type, ...}

.. autoclass:: NoOSPlatform
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Properties

   .. autoproperty:: noos_platform
   .. autoproperty:: noos_project
   .. autoproperty:: hardware_file
   .. autoproperty:: profile
   .. autoproperty:: iiod
   .. autoproperty:: make_variables
   .. autoproperty:: arch

   .. rubric:: Methods

   .. automethod:: get_toolchain
   .. automethod:: validate_toolchain
   .. automethod:: get_make_env

   .. rubric:: Example Usage

   **Basic Xilinx Platform:**

   .. code-block:: python

      from adibuild.platforms.noos import NoOSPlatform

      platform_config = {
          "noos_platform": "xilinx",
          "noos_project": "ad9081_fmca_ebz",
          "hardware_file": "/path/to/system_top.xsa",
          "iiod": False,
          "toolchain": {"preferred": "vivado"},
      }
      platform = NoOSPlatform(platform_config)

      print(platform.noos_platform)   # "xilinx"
      print(platform.noos_project)    # "ad9081_fmca_ebz"
      print(platform.arch)            # "bare_metal"

   **STM32 Platform:**

   .. code-block:: python

      platform_config = {
          "noos_platform": "stm32",
          "noos_project": "cn0565",
          "hardware_file": "/path/to/project.ioc",
          "toolchain": {"preferred": "bare_metal"},
      }
      platform = NoOSPlatform(platform_config)

   **Environment Variables for Make:**

   .. code-block:: python

      # For Xilinx: returns Vivado env vars (XILINX_VITIS, XILINX_VIVADO, PATH)
      env = platform.get_make_env()

Platform → Toolchain Mapping
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - ``noos_platform``
     - Toolchain type
     - Notes
   * - ``xilinx``
     - ``vivado``
     - Vitis/Vivado environment variables injected
   * - ``stm32``
     - ``bare_metal``
     - Requires ``arm-none-eabi-gcc`` in PATH
   * - ``linux``
     - ``system``
     - System GCC for native builds
   * - ``altera``
     - ``system``
     - System GCC for Altera builds
   * - ``aducm3029``
     - ``bare_metal``
     - Requires ``arm-none-eabi-gcc`` in PATH
   * - ``maxim``
     - ``bare_metal``
     - Requires ``arm-none-eabi-gcc`` in PATH
   * - ``pico``
     - ``bare_metal``
     - Requires ``arm-none-eabi-gcc`` in PATH

See Also
--------

- :doc:`noos` (this page) - NoOSPlatform class
- :doc:`../../projects/noos` - NoOSBuilder class
- :doc:`../../user-guide/noos-builds` - User guide for no-OS builds
- :doc:`../core/toolchain` - Toolchain classes
