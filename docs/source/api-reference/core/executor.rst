BuildExecutor
=============

Command execution and build orchestration.

.. currentmodule:: adibuild.core.executor

.. autoclass:: BuildExecutor
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Methods

   .. automethod:: execute
   .. automethod:: execute_stream

   .. rubric:: Example Usage

   **Basic Command Execution:**

   .. code-block:: python

      from adibuild.core.executor import BuildExecutor
      from pathlib import Path

      executor = BuildExecutor(work_dir=Path('/path/to/work'))

      # Execute command
      returncode, stdout, stderr = executor.execute(
          ['ls', '-la'],
          capture_output=True
      )

      if returncode == 0:
          print(f"Output: {stdout}")
      else:
          print(f"Error: {stderr}")

   **Streaming Output:**

   .. code-block:: python

      # Stream output to terminal
      returncode = executor.execute_stream(
          ['make', '-j8'],
          description="Building kernel"
      )

   **Environment Variables:**

   .. code-block:: python

      env = {
          'ARCH': 'arm64',
          'CROSS_COMPILE': 'aarch64-linux-gnu-',
      }

      returncode, _, _ = executor.execute(
          ['make', 'defconfig'],
          env=env
      )

Exceptions
----------

.. autoexception:: BuildError
   :members:
   :undoc-members:
   :show-inheritance:

   .. rubric:: Example Usage

   .. code-block:: python

      from adibuild.core.executor import BuildError

      try:
          returncode, _, _ = executor.execute(['make', 'all'])
          if returncode != 0:
              raise BuildError("Build failed")
      except BuildError as e:
          print(f"Build error: {e}")

See Also
--------

- :doc:`builder` - Builder base class
- :doc:`../projects/linux` - LinuxBuilder usage
