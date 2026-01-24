# pyadi-build Quick Start Guide

Get started with pyadi-build in minutes!

## Installation

### Option 1: Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Verify installation
adibuild --version
```

### Option 2: User Installation

```bash
# Install for current user only
pip install --user .

# Verify installation
adibuild --version
```

## First Build

### 1. Check Available Toolchains

```bash
adibuild toolchain
```

This will detect:
- Xilinx Vivado/Vitis toolchains
- Cached ARM GNU toolchains
- System-installed cross-compilers

Don't worry if none are found - ARM GNU toolchain will be auto-downloaded!

### 2. View Available Platforms

```bash
adibuild config show
```

This shows:
- Available platforms (zynq, zynqmp, microblaze)
- Their configurations
- Device tree blobs (DTBs) and simpleImage targets

### 3. Build Your First Kernel

#### For ZynqMP (ARM64):

```bash
adibuild linux build -p zynqmp -t 2023_R2
```

#### For Zynq (ARM32):

```bash
adibuild linux build -p zynq -t 2023_R2
```

#### For MicroBlaze (Soft-core):

```bash
adibuild linux build -p microblaze -t 2023_R2
```

Note: MicroBlaze requires Xilinx Vivado/Vitis. Source it before building:
```bash
source /opt/Xilinx/Vivado/2023.2/settings64.sh
```

### 4. Find Your Build Artifacts

```bash
ls -l build/linux-2023_R2-*/
```

Output structure:
```
build/linux-2023_R2-arm64/
├── Image                    # Kernel image
├── dts/                     # Device tree blobs
│   ├── zynqmp-zcu102-...dtb
│   └── ...
└── metadata.json            # Build info
```

## Common Tasks

### Build with Custom Options

```bash
# Use more parallel jobs
adibuild linux build -p zynqmp -t 2023_R2 -j 16

# Clean before building
adibuild linux build -p zynq -t 2023_R2 --clean

# Build only DTBs
adibuild linux build -p zynqmp -t 2023_R2 --dtbs-only
```

### Interactive Configuration

```bash
# Run menuconfig
adibuild linux menuconfig -p zynqmp -t 2023_R2

# Then build with custom config
adibuild linux build -p zynqmp -t 2023_R2
```

### Build Specific DTBs

```bash
adibuild linux dtbs -p zynq -t 2023_R2 \
    zynq-zc702-adv7511-ad9361-fmcomms2-3.dtb
```

### Clean Build Artifacts

```bash
# Regular clean
adibuild linux clean -p zynq -t 2023_R2

# Deep clean (mrproper)
adibuild linux clean -p zynq -t 2023_R2 --deep
```

## Using Python API

Create a file `build_kernel.py`:

```python
from adibuild import LinuxBuilder, BuildConfig
from adibuild.platforms import ZynqMPPlatform

# Load configuration
config = BuildConfig.from_yaml('configs/linux/2023_R2.yaml')

# Get platform
platform_config = config.get_platform('zynqmp')
platform = ZynqMPPlatform(platform_config)

# Create builder and build
builder = LinuxBuilder(config, platform)
result = builder.build()

print(f"Build completed in {result['duration']:.1f}s")
print(f"Output: {result['artifacts']}")
```

Run it:
```bash
python build_kernel.py
```

## Troubleshooting

### Problem: "No suitable toolchain found"

**Solution**: Let it auto-download ARM GNU toolchain:
```bash
# Just run the build, ARM GNU toolchain will download automatically
adibuild linux build -p zynqmp -t 2023_R2
```

Or install a system toolchain:
```bash
# Ubuntu/Debian
sudo apt install gcc-arm-linux-gnueabihf gcc-aarch64-linux-gnu

# Fedora/RHEL
sudo dnf install gcc-arm-linux-gnu gcc-aarch64-linux-gnu
```

### Problem: Build is slow

**Solution**: Increase parallel jobs:
```bash
adibuild linux build -p zynqmp -t 2023_R2 -j 16
```

### Problem: Git clone is slow

**Solution**: Use shallow clone (edit config):
```yaml
repository_options:
  depth: 1
```

### Problem: Need more details

**Solution**: Enable verbose mode:
```bash
adibuild -vv linux build -p zynqmp -t 2023_R2
```

Check the log file:
```bash
cat ~/.adibuild/work/build-arm64.log
```

## Configuration

### Global Configuration

Create `~/.adibuild/config.yaml`:

```bash
adibuild config init
```

This sets:
- Default parallel jobs
- Vivado path (if not auto-detected)
- Toolchain cache directory

### Custom Configuration

Create your own config file:

```yaml
# my_config.yaml
project: linux
repository: https://github.com/analogdevicesinc/linux.git
tag: 2023_R2

build:
  parallel_jobs: 16
  output_dir: ./my_builds

platforms:
  zynqmp:
    arch: arm64
    cross_compile: aarch64-linux-gnu-
    defconfig: adi_zynqmp_defconfig
    kernel_target: Image
    dtbs:
      - zynqmp-zcu102-rev10-ad9361-fmcomms2-3.dtb
```

Use it:
```bash
adibuild --config my_config.yaml linux build -p zynqmp
```

## Development Setup

```bash
# Clone repository
git clone https://github.com/analogdevicesinc/pyadi-build.git
cd pyadi-build

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Format code
make format

# Run linting
make lint
```

## Examples

Check the `examples/` directory:

```bash
# Run Zynq example
python examples/build_zynq_kernel.py

# Run ZynqMP example
python examples/build_zynqmp_kernel.py

# Run MicroBlaze example
python examples/build_microblaze_kernel.py

# Run custom config example
python examples/custom_config.py
```

## Need Help?

- Read the full [README.md](README.md)
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for development
- Open an issue on GitHub
- See `adibuild --help` for all commands

## Quick Reference

| Command | Description |
|---------|-------------|
| `adibuild --version` | Show version |
| `adibuild toolchain` | Check toolchains |
| `adibuild config show` | List platforms |
| `adibuild linux build -p <platform> -t <tag>` | Build kernel |
| `adibuild linux menuconfig -p <platform>` | Configure kernel |
| `adibuild linux clean -p <platform>` | Clean build |
| `adibuild -vv` | Verbose mode |

Happy building! 🚀
