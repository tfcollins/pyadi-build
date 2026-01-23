API Reference
=============

Complete Python API documentation for pyadi-build.

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: Core
      :link: core/index
      :link-type: doc
      :text-align: center

      :octicon:`package;2em`

      Core functionality: config, builder, executor, toolchain

   .. grid-item-card:: Projects
      :link: projects/index
      :link-type: doc
      :text-align: center

      :octicon:`repo;2em`

      Project builders: Linux kernel

   .. grid-item-card:: Platforms
      :link: platforms/index
      :link-type: doc
      :text-align: center

      :octicon:`cpu;2em`

      Platform support: Zynq, ZynqMP

   .. grid-item-card:: Utilities
      :link: utils/index
      :link-type: doc
      :text-align: center

      :octicon:`tools;2em`

      Utilities: git, logger, validators

Quick API Overview
------------------

Core Classes
~~~~~~~~~~~~

.. autosummary::
   :nosignatures:

   adibuild.core.config.BuildConfig
   adibuild.core.builder.BuilderBase
   adibuild.core.executor.BuildExecutor
   adibuild.core.toolchain.VivadoToolchain
   adibuild.core.toolchain.ArmToolchain
   adibuild.core.toolchain.SystemToolchain

Project Builders
~~~~~~~~~~~~~~~~

.. autosummary::
   :nosignatures:

   adibuild.projects.linux.LinuxBuilder

Platform Classes
~~~~~~~~~~~~~~~~

.. autosummary::
   :nosignatures:

   adibuild.platforms.base.PlatformBase
   adibuild.platforms.zynq.ZynqPlatform
   adibuild.platforms.zynqmp.ZynqMPPlatform

Utility Classes
~~~~~~~~~~~~~~~

.. autosummary::
   :nosignatures:

   adibuild.utils.git.GitRepository
   adibuild.utils.logger.setup_logging

Common Imports
--------------

Import commonly-used classes:

.. code-block:: python

   # Core functionality
   from adibuild import BuildConfig, LinuxBuilder

   # Platforms
   from adibuild.platforms import ZynqPlatform, ZynqMPPlatform

   # Toolchains
   from adibuild.core.toolchain import VivadoToolchain, ArmToolchain

   # Utilities
   from adibuild.utils.git import GitRepository
   from adibuild.utils.logger import setup_logging

   # Exceptions
   from adibuild.core.executor import BuildError

Package Structure
-----------------

.. code-block:: text

   adibuild/
   ├── __init__.py              # Package exports
   ├── core/                    # Core functionality
   │   ├── config.py            # BuildConfig
   │   ├── builder.py           # BuilderBase
   │   ├── executor.py          # BuildExecutor
   │   └── toolchain.py         # Toolchain classes
   ├── projects/                # Project builders
   │   └── linux.py             # LinuxBuilder
   ├── platforms/               # Platform support
   │   ├── base.py              # PlatformBase
   │   ├── zynq.py              # ZynqPlatform
   │   └── zynqmp.py            # ZynqMPPlatform
   ├── utils/                   # Utilities
   │   ├── git.py               # Git operations
   │   ├── logger.py            # Logging
   │   └── validators.py        # Validation
   └── cli/                     # CLI (see User Guide)

.. toctree::
   :maxdepth: 2
   :hidden:

   core/index
   projects/index
   platforms/index
   utils/index
