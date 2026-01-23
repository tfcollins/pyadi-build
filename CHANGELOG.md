# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-22

### Added
- Initial release of pyadi-build
- Linux kernel builder for ADI projects
- Support for Zynq (ARM32) and ZynqMP (ARM64) platforms
- Automatic toolchain detection and management
  - Xilinx Vivado/Vitis toolchain support
  - ARM GNU toolchain auto-download
  - System toolchain detection
- YAML-based configuration with JSON schema validation
- Rich CLI with progress indicators
- Python API for programmatic builds
- Device tree blob (DTB) building and packaging
- Build artifact packaging with metadata
- Comprehensive test suite
- Examples and documentation

### Features
- Build Linux kernels for ADI platforms
- Auto-detect or download cross-compilation toolchains
- Interactive kernel configuration (menuconfig)
- Parallel builds with configurable job count
- Build artifact packaging and organization
- Git repository caching for faster subsequent builds
- Streaming build output with error highlighting
- Comprehensive logging with file and console outputs

### Documentation
- Complete README with usage examples
- Python API examples
- CLI command reference
- Configuration file documentation
- Toolchain setup guide

### Testing
- Unit tests for all core components
- Integration tests for Linux builder
- Platform-specific tests
- Mock-based tests for fast execution
- Real build tests (optional, slow)
- Test automation with nox

## [Unreleased]

### Changed
- **BREAKING**: Replaced Linaro toolchain with official ARM GNU toolchain
  - Toolchain downloads now come from ARM's official CDN
  - Updated GCC version mapping to match Vitis releases exactly
  - ARM32 prefix changed: `arm-linux-gnueabihf-` → `arm-none-linux-gnueabihf-`
  - ARM64 prefix changed: `aarch64-linux-gnu-` → `aarch64-none-linux-gnu-`
  - Cache directory changed: `~/.adibuild/toolchains/linaro/` → `~/.adibuild/toolchains/arm/`
  - Configuration files: Replace `linaro` with `arm` in toolchain fallback lists
- Version mapping updated for better GCC compatibility:
  - Vitis 2023.2/2023.1 → ARM GNU 12.2.rel1 (GCC 12.2.0)
  - Vitis 2022.2/2022.1 → ARM GNU 11.2-2022.02 (GCC 11.2.0)

### Planned Features
- HDL project builder
- libiio builder
- Additional platform support (Versal, ARM Cortex-A9, RISC-V)
- Build optimization (incremental builds, distributed builds)
- CI/CD integration templates
- Docker images for reproducible builds
- Web UI for build management
