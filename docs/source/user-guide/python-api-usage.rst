Python API Usage
================

This guide shows how to use pyadi-build as a Python library in your own scripts and applications.

Overview
--------

pyadi-build provides a clean Python API for:

- Loading and manipulating build configurations
- Building Linux kernels programmatically
- Managing toolchains
- Accessing build metadata

The API is designed to be simple for basic use cases while providing full control for advanced scenarios.

Quick Start
-----------

Basic Build
~~~~~~~~~~~

Here's a minimal example that builds a ZynqMP kernel:

.. code-block:: python

   from pathlib import Path
   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqMPPlatform

   # Load configuration
   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # Get platform configuration
   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)

   # Create builder and build
   builder = LinuxBuilder(config, platform)
   result = builder.build()

   print(f"Build completed in {result['duration']:.1f}s")
   print(f"Artifacts: {result['artifacts']}")

Core Components
---------------

BuildConfig Class
~~~~~~~~~~~~~~~~~

The :class:`~adibuild.core.config.BuildConfig` class manages build configuration.

**Loading Configuration**

From YAML file:

.. code-block:: python

   from adibuild import BuildConfig

   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

From dictionary:

.. code-block:: python

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

**Accessing Configuration**

.. code-block:: python

   # Get project info
   project = config.get('project')
   repository = config.get('repository')
   tag = config.get('tag')

   # Get platform configuration
   platform_config = config.get_platform('zynqmp')
   arch = platform_config['arch']
   defconfig = platform_config['defconfig']

   # Get build settings
   parallel_jobs = config.get('build.parallel_jobs', default=8)
   output_dir = config.get('build.output_dir', default='./build')

**Modifying Configuration**

.. code-block:: python

   # Change tag
   config.set('tag', 'main')

   # Change parallel jobs
   config.set('build.parallel_jobs', 16)

   # Change output directory
   config.set('build.output_dir', '/tmp/build')

   # Modify platform configuration
   platform_config = config.get_platform('zynqmp')
   platform_config['defconfig'] = 'my_custom_defconfig'
   config.set('platforms.zynqmp', platform_config)

Platform Classes
~~~~~~~~~~~~~~~~

Platform classes encapsulate platform-specific settings:

**ZynqMPPlatform** (ARM64):

.. code-block:: python

   from adibuild.platforms import ZynqMPPlatform

   platform_config = config.get_platform('zynqmp')
   platform = ZynqMPPlatform(platform_config)

   print(f"Architecture: {platform.arch}")           # arm64
   print(f"Defconfig: {platform.defconfig}")         # adi_zynqmp_defconfig
   print(f"Kernel target: {platform.kernel_target}") # Image

**ZynqPlatform** (ARM32):

.. code-block:: python

   from adibuild.platforms import ZynqPlatform

   platform_config = config.get_platform('zynq')
   platform = ZynqPlatform(platform_config)

   print(f"Architecture: {platform.arch}")           # arm
   print(f"Kernel target: {platform.kernel_target}") # uImage

LinuxBuilder Class
~~~~~~~~~~~~~~~~~~

The :class:`~adibuild.projects.linux.LinuxBuilder` class handles Linux kernel builds.

**Creating a Builder**

.. code-block:: python

   from adibuild import LinuxBuilder

   builder = LinuxBuilder(config, platform)

**Building**

Full build (kernel + DTBs):

.. code-block:: python

   result = builder.build()

Build with clean:

.. code-block:: python

   result = builder.build(clean_before=True)

Build only DTBs:

.. code-block:: python

   result = builder.build(dtbs_only=True)

**Build Result**

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

Advanced Usage
--------------

Step-by-Step Build
~~~~~~~~~~~~~~~~~~~

For fine-grained control, use individual build steps:

.. code-block:: python

   from adibuild import LinuxBuilder

   builder = LinuxBuilder(config, platform)

   # Step 1: Prepare source (clone/update repository)
   builder.prepare_source()

   # Step 2: Configure kernel
   builder.configure()

   # Step 3: Build kernel image
   kernel_image = builder.build_kernel()
   print(f"Kernel built: {kernel_image}")

   # Step 4: Build device trees
   dtbs = builder.build_dtbs()
   print(f"Built {len(dtbs)} DTBs")

   # Step 5: Package artifacts
   output_dir = builder.package_artifacts(kernel_image, dtbs)
   print(f"Artifacts: {output_dir}")

Custom Configuration
~~~~~~~~~~~~~~~~~~~~

Run menuconfig for interactive configuration:

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

Building Specific DTBs
~~~~~~~~~~~~~~~~~~~~~~

Build only specific device tree blobs:

.. code-block:: python

   # Build specific DTBs
   dtbs = builder.build_dtbs(dtbs=[
       'zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb',
       'zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb',
   ])

Clean Build
~~~~~~~~~~~

Clean before building:

.. code-block:: python

   builder = LinuxBuilder(config, platform)

   # Clean (make clean)
   builder.clean(deep=False)

   # Deep clean (make mrproper)
   builder.clean(deep=True)

   # Then build
   result = builder.build()

Toolchain Management
--------------------

Detecting Toolchains
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from adibuild.core.toolchain import VivadoToolchain, ArmToolchain, SystemToolchain

   # Check Vivado toolchain
   vivado = VivadoToolchain()
   vivado_info = vivado.detect()
   if vivado_info:
       print(f"Vivado toolchain: {vivado_info['path']}")

   # Check ARM GNU toolchain
   arm = ArmToolchain()
   arm_info = arm.detect()
   if arm_info:
       print(f"ARM GNU toolchain: {arm_info['path']}")

   # Check system toolchain
   system = SystemToolchain()
   system_info = system.detect()
   if system_info:
       print(f"System toolchain: {system_info['cross_compile']}")

Getting Platform Toolchain
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   platform = ZynqMPPlatform(platform_config)
   toolchain = platform.get_toolchain()

   print(f"Selected toolchain: {toolchain['type']}")
   print(f"Cross-compile: {toolchain['cross_compile']}")
   print(f"Version: {toolchain.get('version', 'unknown')}")

Git Operations
--------------

The builder uses :class:`~adibuild.utils.git.GitRepository` for repository management.

Accessing the Repository
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   builder = LinuxBuilder(config, platform)
   builder.prepare_source()

   # Access git repository object
   repo = builder.git_repo

   # Get current commit
   commit = repo.get_current_commit()
   print(f"Current commit: {commit}")

   # Get current branch/tag
   branch = repo.get_current_branch()
   print(f"Current branch: {branch}")

Error Handling
--------------

All build operations can raise :exc:`~adibuild.core.executor.BuildError`:

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.core.executor import BuildError
   from adibuild.platforms import ZynqMPPlatform

   try:
       config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
       platform_config = config.get_platform('zynqmp')
       platform = ZynqMPPlatform(platform_config)

       builder = LinuxBuilder(config, platform)
       result = builder.build()

       print(f"Build succeeded in {result['duration']:.1f}s")

   except BuildError as e:
       print(f"Build failed: {e}")
       # Handle build failure

   except FileNotFoundError as e:
       print(f"Configuration not found: {e}")
       # Handle missing config

   except Exception as e:
       print(f"Unexpected error: {e}")
       # Handle other errors

Practical Examples
------------------

Build Multiple Platforms
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqPlatform, ZynqMPPlatform

   def build_platform(config, platform_name, platform_class):
       platform_config = config.get_platform(platform_name)
       platform = platform_class(platform_config)

       builder = LinuxBuilder(config, platform)
       result = builder.build()

       print(f"{platform_name}: Built in {result['duration']:.1f}s")
       return result

   # Load configuration
   config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

   # Build for both platforms
   zynq_result = build_platform(config, 'zynq', ZynqPlatform)
   zynqmp_result = build_platform(config, 'zynqmp', ZynqMPPlatform)

CI/CD Integration
~~~~~~~~~~~~~~~~~

.. code-block:: python

   import sys
   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.core.executor import BuildError
   from adibuild.platforms import ZynqMPPlatform

   def ci_build():
       try:
           config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

           # Force clean build
           config.set('build.clean_before', True)

           # Use all CPU cores
           import os
           config.set('build.parallel_jobs', os.cpu_count())

           platform_config = config.get_platform('zynqmp')
           platform = ZynqMPPlatform(platform_config)

           builder = LinuxBuilder(config, platform)
           result = builder.build()

           # Verify artifacts exist
           artifacts_dir = result['artifacts']
           kernel_path = artifacts_dir / 'Image'
           if not kernel_path.exists():
               raise BuildError("Kernel image not found")

           print(f"✓ Build successful: {result['duration']:.1f}s")
           return 0

       except BuildError as e:
           print(f"✗ Build failed: {e}", file=sys.stderr)
           return 1

       except Exception as e:
           print(f"✗ Unexpected error: {e}", file=sys.stderr)
           return 2

   if __name__ == '__main__':
       sys.exit(ci_build())

Custom Build Wrapper
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from pathlib import Path
   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.platforms import ZynqMPPlatform, ZynqPlatform

   class CustomKernelBuilder:
       def __init__(self, tag, platform_name):
           self.tag = tag
           self.platform_name = platform_name
           self.config = self._load_config()
           self.platform = self._create_platform()

       def _load_config(self):
           config = BuildConfig.from_yaml(f'configs/linux/{self.tag}.yaml')
           return config

       def _create_platform(self):
           platform_config = self.config.get_platform(self.platform_name)
           if self.platform_name == 'zynq':
               return ZynqPlatform(platform_config)
           elif self.platform_name == 'zynqmp':
               return ZynqMPPlatform(platform_config)
           else:
               raise ValueError(f"Unknown platform: {self.platform_name}")

       def build(self, clean=False, jobs=None):
           if jobs:
               self.config.set('build.parallel_jobs', jobs)

           builder = LinuxBuilder(self.config, self.platform)
           return builder.build(clean_before=clean)

   # Usage
   builder = CustomKernelBuilder('2023_R2', 'zynqmp')
   result = builder.build(clean=True, jobs=16)
   print(f"Built in {result['duration']:.1f}s")

Logging Configuration
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   import logging
   from adibuild.utils.logger import setup_logging

   # Enable debug logging
   setup_logging(level=logging.DEBUG)

   # Or use standard logging
   logging.basicConfig(level=logging.INFO)

   # Now run build
   builder = LinuxBuilder(config, platform)
   result = builder.build()

API Reference
-------------

For complete API documentation, see:

- :doc:`../api-reference/core/config` - BuildConfig class
- :doc:`../api-reference/projects/linux` - LinuxBuilder class
- :doc:`../api-reference/platforms/zynq` - ZynqPlatform class
- :doc:`../api-reference/platforms/zynqmp` - ZynqMPPlatform class
- :doc:`../api-reference/core/toolchain` - Toolchain classes
- :doc:`../api-reference/utils/git` - GitRepository class

Next Steps
----------

- Check :doc:`../examples/python-api/index` for more examples
- See :doc:`../api-reference/index` for complete API documentation
- Learn about :doc:`configuration-guide` for advanced configuration
