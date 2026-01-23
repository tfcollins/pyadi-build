BuilderBase
===========

Abstract base class for all builders.

.. currentmodule:: adibuild.core.builder

.. autoclass:: BuilderBase
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Abstract Methods

   These methods must be implemented by subclasses:

   .. automethod:: prepare_source
   .. automethod:: configure
   .. automethod:: build

   .. rubric:: Usage

   The BuilderBase class is not used directly. Instead, use project-specific builders
   that inherit from this class:

   - :class:`~adibuild.projects.linux.LinuxBuilder` for Linux kernel builds

   **Example Subclass:**

   .. code-block:: python

      from adibuild.core.builder import BuilderBase

      class MyBuilder(BuilderBase):
          def prepare_source(self):
              # Clone/update repository
              pass

          def configure(self):
              # Configure project
              pass

          def build(self, **kwargs):
              # Execute build
              return {
                  'success': True,
                  'duration': 123.4,
                  'artifacts': Path('/path/to/artifacts'),
              }

See Also
--------

- :doc:`../projects/linux` - LinuxBuilder implementation
- :doc:`executor` - Build execution
