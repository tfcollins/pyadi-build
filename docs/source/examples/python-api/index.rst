Python API Examples
===================

Examples using pyadi-build as a Python library.

Basic Build Example
-------------------

.. literalinclude:: ../../../../examples/build_zynqmp_kernel.py
   :language: python
   :linenos:
   :caption: examples/build_zynqmp_kernel.py

Custom Configuration Example
-----------------------------

.. literalinclude:: ../../../../examples/custom_config.py
   :language: python
   :linenos:
   :caption: examples/custom_config.py

Error Handling Example
-----------------------

.. code-block:: python

   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.core.executor import BuildError
   from adibuild.platforms import ZynqMPPlatform
   import sys

   try:
       config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
       platform_config = config.get_platform('zynqmp')
       platform = ZynqMPPlatform(platform_config)

       builder = LinuxBuilder(config, platform)
       result = builder.build()

       print(f"✓ Build succeeded in {result['duration']:.1f}s")
       sys.exit(0)

   except BuildError as e:
       print(f"✗ Build failed: {e}", file=sys.stderr)
       sys.exit(1)

   except FileNotFoundError as e:
       print(f"✗ Configuration not found: {e}", file=sys.stderr)
       sys.exit(2)

   except Exception as e:
       print(f"✗ Unexpected error: {e}", file=sys.stderr)
       sys.exit(3)

CI/CD Integration Example
--------------------------

.. code-block:: python

   import os
   import sys
   from pathlib import Path
   from adibuild import LinuxBuilder, BuildConfig
   from adibuild.core.executor import BuildError
   from adibuild.platforms import ZynqMPPlatform

   def ci_build():
       """CI/CD build with error handling and artifact verification."""
       try:
           # Load configuration
           config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

           # Configure for CI
           config.set('build.clean_before', True)
           config.set('build.parallel_jobs', os.cpu_count())
           config.set('repository_options.depth', 1)

           # Build
           platform_config = config.get_platform('zynqmp')
           platform = ZynqMPPlatform(platform_config)
           builder = LinuxBuilder(config, platform)
           result = builder.build()

           # Verify artifacts
           artifacts_dir = result['artifacts']
           kernel_path = artifacts_dir / 'Image'
           if not kernel_path.exists():
               raise BuildError("Kernel image not found")

           print(f"✓ CI build successful: {result['duration']:.1f}s")
           print(f"✓ Artifacts: {artifacts_dir}")
           return 0

       except Exception as e:
           print(f"✗ CI build failed: {e}", file=sys.stderr)
           return 1

   if __name__ == '__main__':
       sys.exit(ci_build())
