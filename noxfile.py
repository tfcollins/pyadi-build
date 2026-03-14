"""Nox sessions for testing and automation."""

import socket
from pathlib import Path

import nox

# Python versions to test
PYTHON_VERSIONS = ["3.10", "3.11", "3.12"]

# Default sessions
nox.options.sessions = ["tests", "lint"]

ACT_DEFAULT_IMAGE = "catthehacker/ubuntu:act-latest"
ACT_ARTIFACT_DIR = Path(".act") / "artifacts"
ACT_ARTIFACT_ADDR = "127.0.0.1"


def _find_open_port() -> int:
    """Allocate a free local TCP port for ephemeral local services."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((ACT_ARTIFACT_ADDR, 0))
        return sock.getsockname()[1]


def _act_platform_args() -> list[str]:
    """Return default platform mappings for local act runs."""
    return [
        "--pull=false",
        "-P",
        f"ubuntu-latest={ACT_DEFAULT_IMAGE}",
        "-P",
        f"self-hosted={ACT_DEFAULT_IMAGE}",
        "-P",
        f"linux={ACT_DEFAULT_IMAGE}",
        "-P",
        f"x64={ACT_DEFAULT_IMAGE}",
        "--container-architecture",
        "linux/amd64",
    ]


def _run_act(
    session: nox.Session,
    workflow: str,
    event: str,
    default_args: list[str] | None = None,
) -> None:
    """Run a GitHub Actions workflow locally through act."""
    ACT_ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_port = str(_find_open_port())
    act_args = session.posargs or (default_args or [])
    session.run(
        "act",
        event,
        "-W",
        workflow,
        "--action-offline-mode",
        "--artifact-server-addr",
        ACT_ARTIFACT_ADDR,
        "--artifact-server-path",
        str(ACT_ARTIFACT_DIR.resolve()),
        "--artifact-server-port",
        artifact_port,
        *_act_platform_args(),
        *act_args,
        external=True,
    )


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
    session.install(".[dev]", "setuptools<70.0.0", "pyelftools")
    session.run(
        "pytest",
        "-v",
        "-m",
        "real_build and not docker_vivado",
        "--real-build",
        "--tb=short",
        "--maxfail=1",
        "test/integration/",
        *session.posargs,
    )


@nox.session(python=["3.11"])
def tests_real_vivado_docker(session):
    """
    Run the opt-in Docker-backed Vivado installation test.

    Requires Docker, AMD credentials, substantial disk space, and network access.
    """
    session.install(".[dev]", "setuptools<70.0.0", "pyelftools")
    session.run(
        "pytest",
        "-v",
        "-s",
        "test/integration/test_real_vivado_docker_install.py",
        "-m",
        "docker_vivado",
        "--real-build",
        "--tb=short",
        *session.posargs,
    )


@nox.session(python=["3.11"])
def amd_access(session):
    """
    Run the AMD account access integration test.
    """
    session.install(".[vivado-selenium,vivado-browser,vivado-stealth]", "pytest")
    session.run("playwright", "install", "chromium")
    session.run("pytest", "-v", "test/integration/test_amd_account_access.py")


@nox.session(python=["3.11"])
def session_extraction(session):
    """
    Run the session extraction proof of concept.
    """
    session.install(".[vivado-stealth]", "requests")
    # Load credentials from config.sh
    with open("config.sh") as f:
        for line in f:
            if line.startswith("export "):
                key_val = line.strip().split("export ")[1].split("=")
                key = key_val[0]
                val = key_val[1].strip("'")
                session.env[key] = val
    
    session.run("xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python", "test_session_extraction.py")


@nox.session(python=["3.11"])
def selenium_poc(session):
    """
    Run the undetected-chromedriver and Selenium proof of concepts for AMD access.
    """
    session.install(".[vivado-selenium,vivado-stealth]")
    session.run("xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python", "test_uc_amd_v2.py")
    session.run("xvfb-run", "--auto-servernum", "--server-args=-screen 0 1920x1080x24", "python", "test_pw_stealth_v2.py")


@nox.session(python=PYTHON_VERSIONS)
@nox.parametrize("platform", ["zynq", "zynqmp", "microblaze", "boot", "noos"])
def tests_real_platform(session, platform):
    """Run real build tests for specific platform.

    Args:
        platform: Platform to test (zynq, zynqmp, microblaze, boot, or noos)
    """
    session.install(".[dev]", "setuptools<70.0.0", "pyelftools")
    if platform == "boot":
        test_file = "test/integration/test_real_zynqmp_boot.py"
    elif platform == "noos":
        test_file = "test/integration/test_real_noos_build.py"
    else:
        test_file = f"test/integration/test_real_{platform}_build.py"

    session.run(
        "pytest",
        "-v",
        test_file,
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


@nox.session
def act_ci(session):
    """Run the standard GitHub Actions test workflow locally via act."""
    _run_act(session, ".github/workflows/test.yml", "pull_request", ["--job", "lint"])


@nox.session
def act_docs(session):
    """Run the documentation workflow locally via act."""
    _run_act(session, ".github/workflows/docs.yml", "push", ["--job", "build-docs"])


@nox.session
def act_selfhosted(session):
    """Run the self-hosted full test workflow locally via act."""
    _run_act(
        session,
        ".github/workflows/selfhosted-tests.yml",
        "workflow_dispatch",
        ["--job", "lint"],
    )
