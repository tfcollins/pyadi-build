"""
pyadi-build: Build system for ADI projects
===========================================

A Python module to generate and run build commands for ADI projects including
Linux kernel, HDL, and libiio.

Example usage:
    >>> from adibuild import LinuxBuilder, BuildConfig
    >>> from adibuild.platforms import ZynqMPPlatform
    >>> config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')
    >>> platform = ZynqMPPlatform(config.get_platform('zynqmp'))
    >>> builder = LinuxBuilder(config, platform)
    >>> builder.build()
"""

__version__ = "0.1.0"
__author__ = "Analog Devices, Inc."
__license__ = "BSD"

from adibuild.core.builder import BuilderBase
from adibuild.core.config import BuildConfig
from adibuild.projects.linux import LinuxBuilder

__all__ = [
    "__version__",
    "BuildConfig",
    "BuilderBase",
    "LinuxBuilder",
]
