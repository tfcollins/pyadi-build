"""Platform configurations for different hardware architectures."""

from adibuild.platforms.base import Platform
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform

__all__ = ["Platform", "ZynqPlatform", "ZynqMPPlatform"]
