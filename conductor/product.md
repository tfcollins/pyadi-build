# Initial Concept
A Python module to generate and run build commands for Analog Devices, Inc. (ADI) projects including Linux kernel, HDL, and libiio.

## Product Vision
`pyadi-build` aims to provide a unified, robust, and easy-to-use Python-based build system for ADI's hardware and embedded software projects. It simplifies complex build processes for Linux kernels, FPGA bitstreams, and no-OS software by automating toolchain management, containerization, and configuration.

## Key Features
- **Linux Kernel Builder**: Automated ADI Linux kernel builds for Zynq, ZynqMP, and MicroBlaze.
- **Vivado Automation**: Robust AMD Vivado downloads using modular strategies (Docker, session extraction) and automated installation.
- **Docker Integration**: Containerized HDL, no-OS, and boot component builds using reusable Vivado Docker images.
- **Toolchain Management**: Automatic detection and downloading of cross-compilation toolchains.
- **Configuration & Validation**: YAML-based configuration with JSONSchema validation for consistent build environments.
- **Rich CLI & API**: Both a high-quality CLI for end-users and a clean Python API for developers.
- **MCP Server Support**: Integration with Model Context Protocol (MCP) for AI-enhanced workflows.

## Target Audience
- **Embedded Software Engineers**: Building Linux kernels and drivers for ADI platforms.
- **FPGA/HDL Engineers**: Developing and building bitstreams with Vivado.
- **Systems Integrators**: Creating complete boot images (BOOT.BIN, DTBs) for ADI hardware.
- **DevOps Engineers**: Automating hardware build pipelines in CI/CD environments.

## Success Metrics
- **Ease of Use**: Reduced time to first successful build for new ADI projects.
- **Reproducibility**: Consistent build results across different environments via Docker.
- **Maintenance**: Simplified updates to build tools and toolchains.
- **Extensibility**: Ease of adding new platforms, projects, or build targets.
