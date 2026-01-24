"""Pytest configuration and fixtures for example tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_git_repo_for_examples(mocker, mock_kernel_source, mock_toolchain, tmp_path):
    """Mock GitRepository and toolchain for example tests with proper setup."""
    # Mock Path.home() to return a temp directory so repo_cache uses tmp_path
    # This ensures that prepare_source() sets source_dir to tmp_path instead of real home
    mock_home = tmp_path / "home"
    mock_home.mkdir()
    mocker.patch("pathlib.Path.home", return_value=mock_home)

    # Create the expected directory structure and symlink to mock_kernel_source
    # So when LinuxBuilder sets source_dir = repo_cache, it points to our mock
    adibuild_dir = mock_home / ".adibuild" / "repos"
    adibuild_dir.mkdir(parents=True)

    # Create symlink instead of copy, so changes to mock_kernel_source are reflected
    linux_link = adibuild_dir / "linux"
    linux_link.symlink_to(mock_kernel_source)

    # We need to create a special mock that handles the GitRepository initialization
    def mock_init(self, url, local_path, cache_dir=None):
        """Mock __init__ that sets up the repo property correctly."""
        self.url = url
        self.local_path = Path(local_path)
        self.cache_dir = cache_dir or Path.home() / ".adibuild" / "repos"
        self.logger = MagicMock()
        # This is the key: set repo to a MagicMock so it's not None
        self.repo = MagicMock()

    # Patch the __init__ method
    mocker.patch("adibuild.utils.git.GitRepository.__init__", mock_init)

    # Patch all the GitRepository methods
    mocker.patch("adibuild.utils.git.GitRepository.clone", return_value=MagicMock())
    mocker.patch("adibuild.utils.git.GitRepository.fetch", return_value=None)
    mocker.patch("adibuild.utils.git.GitRepository.checkout", return_value=None)
    mocker.patch("adibuild.utils.git.GitRepository.get_commit_sha", return_value="abc123def456")

    # Also patch toolchain selection - need to patch where it's used, not where it's defined
    mocker.patch("adibuild.platforms.base.select_toolchain", return_value=mock_toolchain)

    return None  # No need to return anything
