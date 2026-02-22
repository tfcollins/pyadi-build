"""Nox sessions for testing and automation."""

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

# Default sessions
nox.options.sessions = ["tests", "lint"]


@nox.session(python=PYTHON_VERSIONS)
def tests(session):
    """
    Run unit tests with mocked builds.

    This is the fast test suite that mocks external dependencies.
    """
    session.install(".[dev]")
    session.run(
        "pytest",
        "-v",
        "--cov=adibuild",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-m",
        "not real_build and not toolchain",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS)
def test_examples(session):
    """
    Run example tests to verify examples work correctly.

    Tests the example scripts with mocked dependencies.
    """
    session.install(".[dev]")
    session.run(
        "pytest",
        "-v",
        "test/examples/",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS)
def tests_real(session):
    """
    Run tests with real kernel builds (slow).

    This includes actual kernel compilation and requires toolchains.
    Use with caution as it can take significant time.
    """
    session.install(".[dev]")
    session.run(
        "pytest",
        "-v",
        "-m",
        "real_build",
        "--real-build",
        "--tb=short",
        "--maxfail=1",
        "test/integration/",
        *session.posargs,
    )


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("platform", ["zynq", "zynqmp", "microblaze"])
def tests_real_platform(session, platform):
    """Run real build tests for specific platform.

    Args:
        platform: Platform to test (zynq, zynqmp, or microblaze)
    """
    session.install(".[dev]")
    session.run(
        "pytest",
        "-v",
        f"test/integration/test_real_{platform}_build.py",
        "--real-build",
        "--tb=short",
        *session.posargs,
    )


@nox.session
def lint(session):
    """Run code linters (black and ruff)."""
    session.install("black>=23.0", "ruff>=0.1.0")

    # Check formatting with black
    session.run("black", "--check", "adibuild", "test")

    # Run ruff
    session.run("ruff", "check", "adibuild", "test", *session.posargs)


@nox.session
def format(session):
    """Format code with black."""
    session.install("black>=23.0")
    session.run("black", "adibuild", "test")


@nox.session
def type_check(session):
    """Run type checking with mypy."""
    session.install("mypy", "types-PyYAML", "types-requests")
    session.install(".")
    session.run("mypy", "adibuild", "--ignore-missing-imports")


@nox.session
def coverage(session):
    """Generate coverage report."""
    session.install(".[dev]")
    session.run(
        "pytest",
        "--cov=adibuild",
        "--cov-report=html",
        "--cov-report=term",
        "-m",
        "not real_build and not toolchain",
    )
    session.log("Coverage report generated in htmlcov/index.html")


@nox.session
def docs(session):
    """Build documentation."""
    session.install("-e", ".[docs]")
    session.cd("docs")
    session.run(
        "sphinx-build", "-b", "html", "-W", "-n", "-j", "auto", "source", "build/html"
    )
    session.log("Documentation built in docs/build/html/index.html")


@nox.session
def docs_live(session):
    """Build and serve documentation with live reload."""
    session.install("-e", ".[docs]")
    session.cd("docs")
    session.run("sphinx-autobuild", "source", "build/html", "--open-browser")


@nox.session
def clean(session):
    """Clean build and test artifacts."""
    import shutil
    from pathlib import Path

    # Directories to remove
    dirs_to_remove = [
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".mypy_cache",
        ".ruff_cache",
        "dist",
        "build",
        "*.egg-info",
    ]

    for pattern in dirs_to_remove:
        for path in Path(".").glob(pattern):
            if path.is_dir():
                session.log(f"Removing {path}")
                shutil.rmtree(path)
            elif path.is_file():
                session.log(f"Removing {path}")
                path.unlink()

    session.log("Cleanup complete")
