# Tech Stack

## Core Language & Runtime
- **Python (>=3.10)**: Selected for its rich ecosystem, ease of automation, and developer productivity.
- **UV**: Modern Python package and environment manager for fast dependency resolution and execution.

## CLI & User Interface
- **Click**: Robust framework for creating beautiful and consistent command-line interfaces.
- **Rich**: Provides high-quality visual feedback, including progress indicators and formatted tables.

## Configuration & Validation
- **PyYAML**: Standard for human-readable configuration files.
- **JSONSchema**: Enables formal validation of YAML configurations to ensure build consistency.

## Automation & VCS
- **GitPython**: Provides programmatic access to Git repositories for managing source code (Linux kernel, HDL, etc.).
- **Nox**: Flexible automation tool for running tests, linting, and multi-version builds.

## Browser Automation & Vivado Integration
- **Playwright / Selenium / undetected-chromedriver / playwright-stealth**: Used for automating Vivado downloads and authenticated AMD account access with anti-bot evasions.

## Ecosystem & Extensions
- **FastMCP (Optional)**: Integration with the Model Context Protocol for AI-enhanced workflows.
- **Docker**: Containerization for reproducible build environments, particularly for FPGA/HDL builds.

## Development & Quality Assurance
- **Setuptools**: Standard build-backend for packaging the library.
- **Pytest**: Industry-standard testing framework.
- **Ruff**: Extremely fast Python linter and formatter.
