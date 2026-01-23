PlatformBase
============

Abstract base class for all platforms.

.. currentmodule:: adibuild.platforms.base

.. autoclass:: PlatformBase
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

   .. rubric:: Abstract Methods

   Subclasses may override these methods:

   .. automethod:: get_toolchain
   .. automethod:: validate_config

   .. rubric:: Usage

   The PlatformBase class is not used directly. Instead, use platform-specific
   classes:

   - :class:`~adibuild.platforms.zynq.ZynqPlatform` for Zynq (ARM32)
   - :class:`~adibuild.platforms.zynqmp.ZynqMPPlatform` for ZynqMP (ARM64)

See Also
--------

- :doc:`zynq` - Zynq platform
- :doc:`zynqmp` - ZynqMP platform
- :doc:`../../user-guide/platforms` - Platform guide
