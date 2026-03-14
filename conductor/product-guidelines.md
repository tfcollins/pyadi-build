# Product Guidelines

## Design Principles
- **Clarity over Cleverness**: Prioritize readable, maintainable code over complex abstractions.
- **Fail Fast**: Build processes should detect and report configuration or tool errors as early as possible.
- **Explicit over Implicit**: Ensure that build steps, toolchain selections, and configuration sources are clear and logged.
- **Reproducibility**: Every build should be repeatable in a clean environment (e.g., Docker).

## User Experience (CLI)
- **Rich Feedback**: Use visual indicators (progress bars, tables, colors) to provide clear status updates during long-running builds.
- **Beautiful Output**: Leverage `rich` to format CLI output for readability and visual appeal.
- **Informative Error Messages**: Provide actionable error messages that guide the user to a resolution.
- **Consistent Command Structure**: Maintain a logical and predictable hierarchy of CLI commands.

## Documentation & Code Style
- **Type Safety**: Use Python type hints throughout the codebase.
- **Docstrings**: Provide clear Google-style docstrings for all public APIs.
- **Exhaustive Testing**: Aim for high test coverage, particularly for core build logic and platform support.
- **Clean API**: Ensure the internal library API is well-structured and easy to use as a dependency.

## Quality Standards
- **Linting & Formatting**: Enforce strict linting and formatting standards (e.g., Ruff).
- **Validation**: All YAML configurations MUST be validated against their respective schemas.
- **Cross-Platform Compatibility**: Ensure tools work consistently across major Linux distributions (Ubuntu, RHEL, etc.).
