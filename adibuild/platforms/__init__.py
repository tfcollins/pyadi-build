"""Platform configurations for different hardware architectures."""

from adibuild.platforms.base import Platform
from adibuild.platforms.lib import LibPlatform
from adibuild.platforms.microblaze import MicroBlazePlatform
from adibuild.platforms.noos import NoOSPlatform
from adibuild.platforms.versal import VersalPlatform
from adibuild.platforms.zynq import ZynqPlatform
from adibuild.platforms.zynqmp import ZynqMPPlatform

__all__ = [
    "Platform",
    "ZynqPlatform",
    "ZynqMPPlatform",
    "VersalPlatform",
    "MicroBlazePlatform",
    "NoOSPlatform",
    "HDLPlatform",
    "LibPlatform",
]
