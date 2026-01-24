# pyadi-build

Python module to generate and run build commands for Analog Devices, Inc. (ADI) projects including Linux kernel, HDL, and libiio.

## Features

- **Linux Kernel Builder**: Build ADI Linux kernels for Zynq, ZynqMP, and MicroBlaze platforms
- **Automatic Toolchain Management**: Auto-detect or download cross-compilation toolchains
- **Configuration Management**: YAML-based configuration with schema validation
- **Multiple Platform Support**: Zynq (ARM32), ZynqMP (ARM64), and MicroBlaze (soft-core) platforms
- **Device Tree Support**: Build and package device tree blobs (DTBs)
- **Rich CLI**: Beautiful command-line interface with progress indicators
- **Python API**: Use as a library in your own Python scripts

## Installation

```bash
pip install pyadi-build
```

For development:

```bash
git clone https://github.com/analogdevicesinc/pyadi-build.git
cd pyadi-build
pip install -e ".[dev]"
```

## Quick Start

### Build a Zynq Kernel

```bash
adibuild linux build -p zynq -t 2023_R2
```

### Build a ZynqMP Kernel

```bash
adibuild linux build -p zynqmp -t 2023_R2
```

### Build a MicroBlaze Kernel

```bash
adibuild linux build -p microblaze -t 2023_R2
```

### List Available Platforms

```bash
adibuild config show
```

### Check Available Toolchains

```bash
adibuild toolchain
```

## Usage

### Command-Line Interface

#### Build Commands

```bash
# Build with default configuration
adibuild linux build -p zynqmp -t 2023_R2

# Build with clean
adibuild linux build -p zynq -t 2023_R2 --clean

# Build only device tree blobs
adibuild linux build -p zynqmp --dtbs-only

# Specify number of parallel jobs
adibuild linux build -p zynq -t 2023_R2 -j 16

# Use custom configuration file
adibuild linux build -p zynqmp -t 2023_R2 --config my_config.yaml
```

#### Configuration Commands

```bash
# Run kernel menuconfig
adibuild linux menuconfig -p zynq -t 2023_R2

# Configure without building
adibuild linux configure -p zynqmp -t 2023_R2

# Build specific DTBs
adibuild linux dtbs -p zynq -t 2023_R2 zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb

# Clean build artifacts
adibuild linux clean -p zynq
```

#### Toolchain Commands

```bash
# Detect available toolchains
adibuild toolchain

# Show toolchain for specific platform
adibuild toolchain -p zynqmp
```

#### Configuration Management

```bash
# Initialize global configuration
adibuild config init

# Show available platforms
adibuild config show

# Validate configuration file
adibuild config validate my_config.yaml
```

### Python API

```python
from adibuild import LinuxBuilder, BuildConfig
from adibuild.platforms import ZynqMPPlatform

# Load configuration
config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

# Get platform configuration
platform_config = config.get_platform('zynqmp')
platform = ZynqMPPlatform(platform_config)

# Create builder
builder = LinuxBuilder(config, platform)

# Build
result = builder.build()

print(f"Build completed in {result['duration']:.1f}s")
print(f"Artifacts: {result['artifacts']}")
```

## Configuration

### Configuration Files

Configuration files are in YAML format:

```yaml
project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2

build:
  parallel_jobs: 8
  clean_before: false
  output_dir: ./build

platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
    dtb_path: arch/arm64/boot/dts/xilinx
    kernel_image_path: arch/arm64/boot/Image

    dtbs:
      - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
      - zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb

    toolchain:
      preferred: vivado
      fallback:
        - arm
        - system
```

### Default Configurations

Pre-configured files are available in `configs/linux/`:
- `2023_R2.yaml` - Full configuration for tag 2023_R2
- `zynq.yaml` - Zynq platform defaults
- `zynqmp.yaml` - ZynqMP platform defaults

### Global Configuration

Create a global configuration at `~/.adibuild/config.yaml`:

```bash
adibuild config init
```

This allows you to set default preferences like:
- Default parallel jobs
- Vivado/Vitis installation path
- Toolchain cache directory

## Toolchains

pyadi-build supports three types of toolchains:

### 1. Xilinx Vivado/Vitis Toolchain (Preferred)

If you have Xilinx Vivado or Vitis installed, pyadi-build will automatically detect and use the included ARM toolchains.

Typical installation paths:
- `/opt/Xilinx/Vitis/`
- `/opt/Xilinx/Vivado/`
- `/tools/Xilinx/Vitis/`

Or set `XILINX_VIVADO` or `XILINX_VITIS` environment variables.

### 2. ARM GNU Toolchain (Auto-download)

If Vivado is not available, pyadi-build will automatically download the appropriate ARM GNU toolchain:

- **ARM32**: `arm-none-linux-gnueabihf-gcc`
- **ARM64**: `aarch64-none-linux-gnu-gcc`

Toolchains are cached in `~/.adibuild/toolchains/arm/`

Version mapping (matching Vitis GCC versions):
- Vivado 2023.2 → ARM GNU 12.2.rel1 (GCC 12.2.0)
- Vivado 2023.1 → ARM GNU 12.2.rel1 (GCC 12.2.0)
- Vivado 2022.2 → ARM GNU 11.2-2022.02 (GCC 11.2.0)
- Vivado 2022.1 → ARM GNU 11.2-2022.02 (GCC 11.2.0)

### 3. System Toolchain

If you have cross-compilers installed on your system:

```bash
# Ubuntu/Debian
sudo apt install gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu

# Fedora/RHEL
sudo dnf install gcc-arm-linux-gnu gcc-aarch64-linux-gnu
```

## Build Outputs

Build artifacts are placed in `./build/linux-{tag}-{platform}/`:

```
build/
└── linux-2023_R2-arm64/
    ├── Image                    # Kernel image
    ├── dts/                     # Device tree blobs
    │   ├── zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
    │   └── zynqmp-zcu102-rev10-ad9364-fmcomms4.dtb
    └── metadata.json            # Build metadata
```

The `metadata.json` file contains:
- Project and platform information
- Git commit SHA
- Build date and duration
- Toolchain details
- List of artifacts

## Supported Platforms

### Zynq (ARM32)

- **Architecture**: ARM Cortex-A9
- **Defconfig**: `zynq_xcomm_adv7511_defconfig`
- **Kernel Target**: `uImage`
- **Toolchain**: `arm-linux-gnueabihf-`

Supported boards:
- ZC702, ZC706, ZedBoard
- Custom Zynq boards with ADI FMC cards

### ZynqMP (ARM64)

- **Architecture**: ARM Cortex-A53
- **Defconfig**: `adi_zynqmp_defconfig`
- **Kernel Target**: `Image`
- **Toolchain**: `aarch64-linux-gnu-`

Supported boards:
- ZCU102
- Custom ZynqMP boards with ADI FMC cards

### MicroBlaze (Soft-core)

- **Architecture**: MicroBlaze soft-core processor
- **Defconfig**: `adi_mb_defconfig`
- **Kernel Target**: `simpleImage.<dts>`
- **Toolchain**: `microblazeel-xilinx-linux-gnu-`

Supported boards:
- VCU118 (Virtex UltraScale+ FPGA)
- KC705, KCU105, VC707, VCU128 (Virtex FPGAs)
- Custom Virtex boards with ADI FMC cards

**Note:** MicroBlaze kernels use `simpleImage` format with embedded device tree, not separate DTB files.

## Development

### Running Tests

```bash
# Run fast unit tests (mocked)
nox -s tests

# Run all tests for all Python versions
nox

# Run linting
nox -s lint

# Format code
nox -s format
```

#### Real Build Integration Tests

Optional integration tests that perform actual kernel builds:

```bash
# Run all real build tests (requires toolchains, ~30-60 minutes)
nox -s tests_real

# Run real builds for specific platform
nox -s tests_real_platform-zynq
nox -s tests_real_platform-zynqmp
nox -s tests_real_platform-microblaze

# Run with pytest directly
pytest --real-build test/integration/

# Run specific test
pytest --real-build test/integration/test_real_zynq_build.py::TestRealZynqBuild::test_full_zynq_build
```

**Requirements for real builds**:
- Toolchain installed (Vivado, ARM GNU, or system cross-compiler)
- Network connectivity (git clone from GitHub)
- Sufficient disk space (~15GB)
- Time (~10-30 minutes per platform)

**What gets tested**:
- Real git clone of analogdevicesinc/linux repository
- Actual kernel configuration (defconfig)
- Real kernel compilation with cross-compiler
- Device tree blob compilation
- Artifact packaging and metadata generation
- File validation (sizes, magic bytes, directory structure)

### Testing Examples

The example scripts have automated tests to verify they work correctly:

```bash
# Run example tests
nox -s test_examples

# Or with pytest directly
pytest test/examples/ -v

# Run integration tests
pytest test/examples/ -v -m integration
```

All example tests use mocked dependencies (git, make, toolchains) for fast execution.

### Project Structure

```
pyadi-build/
├── adibuild/                  # Main package
│   ├── core/                  # Core functionality
│   │   ├── builder.py         # Abstract builder
│   │   ├── config.py          # Configuration management
│   │   ├── executor.py        # Command execution
│   │   └── toolchain.py       # Toolchain management
│   ├── projects/              # Project builders
│   │   └── linux.py           # Linux kernel builder
│   ├── platforms/             # Platform support
│   │   ├── base.py            # Base platform
│   │   ├── zynq.py            # Zynq platform
│   │   ├── zynqmp.py          # ZynqMP platform
│   │   └── microblaze.py      # MicroBlaze platform
│   ├── cli/                   # CLI interface
│   │   ├── main.py            # Click commands
│   │   └── helpers.py         # CLI utilities
│   └── utils/                 # Utilities
│       ├── git.py             # Git operations
│       ├── logger.py          # Logging
│       └── validators.py      # Validation
├── configs/                   # Default configurations
├── test/                      # Test suite
└── examples/                  # Usage examples
```

## Requirements

- Python 3.10 or later
- Git
- Make
- Cross-compilation toolchain (auto-downloaded if needed)
- For menuconfig: ncurses libraries

## Troubleshooting

### Toolchain not found

If you see "No suitable toolchain found":

1. Install Xilinx Vivado/Vitis, or
2. Let pyadi-build download ARM GNU toolchain automatically, or
3. Install system toolchain:
   ```bash
   sudo apt install gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu
   ```

### Build fails

Check the build log:
```
~/.adibuild/work/build-arm64.log
```

Enable verbose output:
```bash
adibuild -vv linux build -p zynqmp -t 2023_R2
```

### Git clone slow

Use shallow clone by setting in configuration:
```yaml
repository_options:
  depth: 1
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

BSD 3-Clause License

## Credits

Developed by Analog Devices, Inc.

## Links

- [GitHub Repository](https://github.com/analogdevicesinc/pyadi-build)
- [Issue Tracker](https://github.com/analogdevicesinc/pyadi-build/issues)
- [ADI GitHub](https://github.com/analogdevicesinc)
- [ADI Linux Kernel](https://github.com/analogdevicesinc/linux)
