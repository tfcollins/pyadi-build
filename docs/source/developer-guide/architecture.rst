Architecture
============

System design and architecture overview for pyadi-build.

High-Level Architecture
------------------------

.. mermaid::

   graph TB
       CLI[CLI Interface] --> Config[BuildConfig]
       Config --> Platform[Platform]
       Config --> Builder[Builder]
       Platform --> Toolchain[Toolchain]
       Builder --> Executor[Executor]
       Builder --> Git[GitRepository]
       Executor --> Make[Make/Build Commands]
       Git --> Repo[Repository]

       subgraph Builders
       Builder --> Linux[LinuxBuilder]
       Builder --> HDL[HDLBuilder]
       end

       style CLI fill:#005c9a,stroke:#333,stroke-width:2px,color:#fff
       style Builder fill:#4dabf7,stroke:#333,stroke-width:2px,color:#fff
       style Executor fill:#a5d8ff,stroke:#333,stroke-width:2px
       style Config fill:#e7f5ff,stroke:#333,stroke-width:2px

Components
----------

Core Components
~~~~~~~~~~~~~~~

**BuildConfig**
   Manages YAML configuration files and provides access to build settings

**BuilderBase**
   Abstract base class defining the builder interface

**BuildExecutor**
   Handles command execution and build orchestration

**Toolchain Classes**
   Detect and manage cross-compilation toolchains

Platform Components
~~~~~~~~~~~~~~~~~~~

**PlatformBase**
   Abstract base class for platform-specific logic

**ZynqPlatform / ZynqMPPlatform**
   Platform-specific implementations for Zynq and ZynqMP

Project Builders
~~~~~~~~~~~~~~~~

**LinuxBuilder**
   Implements Linux kernel build workflow

Utilities
~~~~~~~~~

**GitRepository**
   Git operations (clone, update, checkout)

**Logger**
   Logging configuration

**Validators**
   Configuration validation

Build Workflow
--------------

.. mermaid::

   sequenceDiagram
       participant User
       participant CLI
       participant Builder
       participant Platform
       participant Toolchain
       participant Executor
       participant Git

       User->>CLI: adibuild linux build
       CLI->>Builder: create LinuxBuilder
       Builder->>Platform: get platform config
       Platform->>Toolchain: detect toolchain
       Toolchain-->>Platform: toolchain info
       Builder->>Git: clone/update repository
       Git-->>Builder: repository ready
       Builder->>Executor: run defconfig
       Executor-->>Builder: configured
       Builder->>Executor: run make
       Executor-->>Builder: kernel built
       Builder->>Executor: build DTBs
       Executor-->>Builder: DTBs built
       Builder->>Builder: package artifacts
       Builder-->>CLI: build result
       CLI-->>User: success!

Class Hierarchy
---------------

.. mermaid::

   classDiagram
      class BuilderBase {
          <<abstract>>
          +build()
          +prepare_source()
      }
      class LinuxBuilder {
          +configure()
          +menuconfig()
      }
      class HDLBuilder {
          +build_win()
          +check_version()
      }
      BuilderBase <|-- LinuxBuilder
      BuilderBase <|-- HDLBuilder

      class PlatformBase {
          <<abstract>>
          +get_toolchain()
      }
      class ZynqPlatform
      class ZynqMPPlatform
      class HDLPlatform
      PlatformBase <|-- ZynqPlatform
      PlatformBase <|-- ZynqMPPlatform
      PlatformBase <|-- HDLPlatform

      style BuilderBase fill:#f9f,stroke:#333
      style PlatformBase fill:#f9f,stroke:#333

Key Design Decisions
--------------------

Configuration Management
~~~~~~~~~~~~~~~~~~~~~~~~

YAML-based configuration for:

- Human-readable and editable
- Version control friendly
- Schema validation support
- Hierarchical structure

Platform Abstraction
~~~~~~~~~~~~~~~~~~~~

Platform classes encapsulate:

- Architecture-specific settings
- Toolchain selection logic
- Platform-specific build steps

This allows easy addition of new platforms.

Toolchain Auto-Download
~~~~~~~~~~~~~~~~~~~~~~~

ARM GNU toolchains are automatically downloaded when:

- Vivado/Vitis not available
- System toolchain not installed
- Ensures builds work out-of-the-box

Artifact Packaging
~~~~~~~~~~~~~~~~~~

Build artifacts are organized by:

- Tag/branch name
- Architecture
- Includes metadata.json for traceability

Module Structure
----------------

.. code-block:: text

   adibuild/
   ├── __init__.py              # Package exports
   ├── core/                    # Core functionality (1,358 lines)
   │   ├── __init__.py
   │   ├── config.py            # BuildConfig (287 lines)
   │   ├── builder.py           # BuilderBase (156 lines)
   │   ├── executor.py          # BuildExecutor (368 lines)
   │   └── toolchain.py         # Toolchain classes (547 lines)
   ├── projects/                # Project builders (386 lines)
   │   ├── __init__.py
   │   └── linux.py             # LinuxBuilder (386 lines)
   ├── platforms/               # Platform support (464 lines)
   │   ├── __init__.py
   │   ├── base.py              # PlatformBase (142 lines)
   │   ├── zynq.py              # ZynqPlatform (161 lines)
   │   └── zynqmp.py            # ZynqMPPlatform (161 lines)
   ├── utils/                   # Utilities (545 lines)
   │   ├── __init__.py
   │   ├── git.py               # GitRepository (234 lines)
   │   ├── logger.py            # Logging (87 lines)
   │   └── validators.py        # Validation (224 lines)
   └── cli/                     # CLI interface (698 lines)
       ├── __init__.py
       ├── main.py              # Click commands (483 lines)
       └── helpers.py           # CLI utilities (215 lines)

Total: ~3,451 lines of implementation code

Extending pyadi-build
---------------------

Adding a New Platform
~~~~~~~~~~~~~~~~~~~~~

1. Create new platform class:

   .. code-block:: python

      from adibuild.platforms.base import PlatformBase

      class MyPlatform(PlatformBase):
          def __init__(self, config):
              super().__init__(config)
              # Platform-specific initialization

          def get_toolchain(self):
              # Implement toolchain selection
              pass

2. Register in ``adibuild/platforms/__init__.py``

3. Add platform configuration schema

4. Create default configuration file

Adding a New Project Type
~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Create new builder:

   .. code-block:: python

      from adibuild.core.builder import BuilderBase

      class HDLBuilder(BuilderBase):
          def prepare_source(self):
              # Clone HDL repository
              pass

          def configure(self):
              # Configure HDL project
              pass

          def build(self, **kwargs):
              # Build HDL project
              pass

2. Register in ``adibuild/projects/__init__.py``

3. Add CLI commands in ``adibuild/cli/main.py``

Testing Strategy
----------------

Unit Tests
~~~~~~~~~~

- Mock external dependencies (git, make)
- Fast execution (~1-2 seconds)
- High code coverage

Integration Tests
~~~~~~~~~~~~~~~~~

- Real builds on CI/CD
- Slower but validates full workflow

Example Tests
~~~~~~~~~~~~~

- Verify example scripts work correctly
- Mock dependencies for speed

See Also
--------

- :doc:`contributing` - Contributing guide
- :doc:`../api-reference/index` - API reference
