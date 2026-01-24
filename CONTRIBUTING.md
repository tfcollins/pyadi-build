# Contributing to pyadi-build

Thank you for your interest in contributing to pyadi-build! This document provides guidelines and instructions for contributing.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Create a new branch for your feature or bugfix
4. Make your changes
5. Run tests and linting
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10 or later
- Git
- Make (optional, for convenience commands)

### Installation

```bash
git clone https://github.com/yourusername/pyadi-build.git
cd pyadi-build
pip install -e ".[dev]"
```

## Development Workflow

### Running Tests

#### Fast Unit Tests (Recommended for PRs)

```bash
# Run fast unit tests with mocks
make test
# or
nox -s tests

# Run all tests for all Python versions
make test-all
# or
nox

# Run specific test file
pytest test/core/test_config.py -v
```

**Before submitting PR**: Run fast tests to ensure they pass. CI will run both fast and real build tests.

#### Real Build Integration Tests

These tests perform actual kernel builds and are slower but more comprehensive:

```bash
# Run all real build integration tests (requires toolchains, ~30-60 minutes)
nox -s tests_real

# Run real builds for specific platform
nox -s tests_real_platform-zynq
nox -s tests_real_platform-zynqmp
nox -s tests_real_platform-microblaze
```

**Real build test requirements**:
- Toolchain installed (Vivado, ARM GNU, or system cross-compiler)
- Network connectivity (git clone from GitHub)
- Sufficient disk space (~15GB)

**Skip real build tests by default**: Integration tests are skipped unless `--real-build` flag is used

### Code Style

We use `black` for code formatting and `ruff` for linting.

```bash
# Format code
make format
# or
nox -s format

# Check linting
make lint
# or
nox -s lint
```

### Before Submitting

1. **Run the test suite**: Ensure all tests pass
2. **Format your code**: Run `make format`
3. **Check linting**: Run `make lint`
4. **Update documentation**: If you add features, update README.md
5. **Add tests**: New features should include tests
6. **Update CHANGELOG.md**: Add an entry describing your changes

## Code Guidelines

### Python Style

- Follow PEP 8
- Use type hints for function signatures
- Use Google-style docstrings
- Maximum line length: 100 characters

Example:

```python
def my_function(param1: str, param2: int) -> bool:
    """
    Brief description of function.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong
    """
    pass
```

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in present tense (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable

Example:
```
Add support for Versal platform

- Implement Versal platform class
- Add Versal configuration
- Add tests for Versal platform

Fixes #123
```

### Testing

- Write tests for new features
- Maintain or improve code coverage
- Use fixtures from conftest.py
- Mock external dependencies (git, make, etc.)

Example test:

```python
def test_my_feature(zynq_config):
    """Test my new feature."""
    # Arrange
    builder = LinuxBuilder(zynq_config, platform)

    # Act
    result = builder.my_feature()

    # Assert
    assert result is True
```

## Adding New Features

### Adding a New Platform

1. Create platform class in `adibuild/platforms/`
2. Extend `Platform` base class
3. Implement required methods
4. Add configuration in `configs/linux/`
5. Add tests in `test/linux/`
6. Update documentation

### Adding a New Project Type (e.g., HDL)

1. Create project builder in `adibuild/projects/`
2. Extend `BuilderBase` class
3. Implement all abstract methods
4. Add CLI commands in `adibuild/cli/main.py`
5. Add configuration schema
6. Add comprehensive tests
7. Update documentation

## Pull Request Process

1. **Create a feature branch**: `git checkout -b feature/my-feature`
2. **Make your changes**: Follow the guidelines above
3. **Commit your changes**: Use clear commit messages
4. **Push to your fork**: `git push origin feature/my-feature`
5. **Submit a pull request**: Describe your changes clearly

### Pull Request Checklist

- [ ] Tests pass (`make test`)
- [ ] Code is formatted (`make format`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated
- [ ] Commit messages are clear
- [ ] PR description explains the changes

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the issue
2. **Steps to reproduce**: How to reproduce the issue
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: OS, Python version, pyadi-build version
6. **Logs**: Relevant log output or error messages

## Questions and Support

- Open an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Be respectful and constructive in discussions

## License

By contributing to pyadi-build, you agree that your contributions will be licensed under the BSD 3-Clause License.
