Toolchain Classes
=================

Toolchain detection and management.

.. currentmodule:: adibuild.core.toolchain

Overview
--------

pyadi-build supports three toolchain types:

- :class:`VivadoToolchain` - Xilinx Vivado/Vitis bundled toolchains
- :class:`ArmToolchain` - ARM GNU toolchains (auto-downloaded)
- :class:`SystemToolchain` - System-installed cross-compilers

VivadoToolchain
---------------

.. autoclass:: VivadoToolchain
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: detect
   .. automethod:: get_toolchain

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild.core.toolchain import VivadoToolchain

      vivado = VivadoToolchain()

      # Detect Vivado installation
      info = vivado.detect()
      if info:
          print(f"Vivado path: {info['path']}")
          print(f"Version: {info['version']}")

      # Get toolchain for specific architecture
      arm64_toolchain = vivado.get_toolchain('arm64')
      if arm64_toolchain:
          print(f"ARM64 toolchain: {arm64_toolchain['cross_compile']}")

ArmToolchain
------------

.. autoclass:: ArmToolchain
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: detect
   .. automethod:: get_toolchain
   .. automethod:: download

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild.core.toolchain import ArmToolchain

      arm = ArmToolchain()

      # Detect cached ARM GNU toolchain
      info = arm.detect()
      if info:
          print(f"ARM GNU toolchain: {info['path']}")
      else:
          # Download toolchain
          print("Downloading ARM GNU toolchain...")
          arm.download('arm64', version='12.2.rel1')

      # Get toolchain
      arm64_toolchain = arm.get_toolchain('arm64')
      print(f"Cross-compile: {arm64_toolchain['cross_compile']}")

SystemToolchain
---------------

.. autoclass:: SystemToolchain
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: detect
   .. automethod:: get_toolchain

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild.core.toolchain import SystemToolchain

      system = SystemToolchain()

      # Detect system-installed cross-compiler
      info = system.detect()
      if info:
          print(f"System toolchain found")
          print(f"ARM64: {info.get('arm64')}")
          print(f"ARM32: {info.get('arm32')}")

      # Get specific toolchain
      arm64_toolchain = system.get_toolchain('arm64')
      if arm64_toolchain:
          print(f"Cross-compile: {arm64_toolchain['cross_compile']}")

Toolchain Selection
-------------------

Example showing toolchain selection with fallback:

.. code-block:: python

   from adibuild.core.toolchain import VivadoToolchain, ArmToolchain, SystemToolchain

   def get_best_toolchain(arch='arm64'):
       # Try Vivado first
       vivado = VivadoToolchain()
       info = vivado.detect()
       if info:
           return vivado.get_toolchain(arch)

       # Try ARM GNU second
       arm = ArmToolchain()
       info = arm.detect()
       if info:
           return arm.get_toolchain(arch)

       # Try system toolchain last
       system = SystemToolchain()
       info = system.detect()
       if info:
           return system.get_toolchain(arch)

       raise RuntimeError(f"No toolchain found for {arch}")

   toolchain = get_best_toolchain('arm64')
   print(f"Selected: {toolchain['type']}")
   print(f"Cross-compile: {toolchain['cross_compile']}")

See Also
--------

- :doc:`../../../user-guide/toolchain-management` - Toolchain management guide
- :doc:`../platforms/index` - Platform-specific toolchain usage
