from enum import Enum

class DeviceType(Enum):
    """Device types."""
    SOM = 1
    FMC = 2
    FPGA_CARRIER = 3
    FPGA_FMC = 4