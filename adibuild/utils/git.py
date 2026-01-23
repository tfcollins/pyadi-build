"""Git repository management utilities."""

import shutil
from pathlib import Path
from typing import Optional

import git

from adibuild.utils.logger import get_logger


class RepositoryError(Exception):
    """Exception raised for repository operation errors."""

    pass


class GitRepository:
    """Manages git repository operations with caching support."""

    def __init__(self, url: str, local_path: Path, cache_dir: Optional[Path] = None):
        """
        Initialize GitRepository.

        Args:
            url: Git repository URL
            local_path: Local path where repository should be cloned/cached
            cache_dir: Optional cache directory (defaults to ~/.adibuild/repos/)
        """
        self.url = url
        self.local_path = Path(local_path)
        self.cache_dir = cache_dir or Path.home() / ".adibuild" / "repos"
        self.logger = get_logger("adibuild.git")
        self.repo: Optional[git.Repo] = None

    def clone(self, depth: Optional[int] = None, branch: Optional[str] = None) -> git.Repo:
        """
        Clone repository if it doesn't exist locally.

        Args:
            depth: Optional depth for shallow clone
            branch: Optional specific branch to clone

        Returns:
            git.Repo object

        Raises:
            RepositoryError: If clone operation fails
        """
        if self.local_path.exists():
            self.logger.info(f"Repository already exists at {self.local_path}")
            try:
                self.repo = git.Repo(self.local_path)
                return self.repo
            except git.exc.InvalidGitRepositoryError:
                self.logger.warning(f"Invalid git repository at {self.local_path}, removing...")
                shutil.rmtree(self.local_path)

        self.logger.info(f"Cloning {self.url} to {self.local_path}...")
        self.local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            kwargs = {}
            if depth:
                kwargs["depth"] = depth
            if branch:
                kwargs["branch"] = branch

            self.repo = git.Repo.clone_from(self.url, self.local_path, **kwargs)
            self.logger.info(f"Successfully cloned repository")
            return self.repo

        except git.exc.GitCommandError as e:
            raise RepositoryError(f"Failed to clone repository: {e}") from e

    def fetch(self, remote: str = "origin", tags: bool = True) -> None:
        """
        Fetch latest changes from remote.

        Args:
            remote: Remote name (default: origin)
            tags: Fetch tags (default: True)

        Raises:
            RepositoryError: If fetch operation fails
        """
        if not self.repo:
            raise RepositoryError("Repository not initialized. Call clone() first.")

        self.logger.info(f"Fetching from {remote}...")
        try:
            fetch_info = self.repo.remotes[remote].fetch(tags=tags)
            self.logger.debug(f"Fetched {len(fetch_info)} refs")
        except git.exc.GitCommandError as e:
            raise RepositoryError(f"Failed to fetch from {remote}: {e}") from e

    def checkout(self, ref: str, force: bool = False) -> None:
        """
        Checkout specific reference (branch, tag, commit).

        Args:
            ref: Reference to checkout
            force: Force checkout even with uncommitted changes

        Raises:
            RepositoryError: If checkout operation fails
        """
        if not self.repo:
            raise RepositoryError("Repository not initialized. Call clone() first.")

        self.logger.info(f"Checking out {ref}...")
        try:
            self.repo.git.checkout(ref, force=force)
            self.logger.info(f"Successfully checked out {ref}")
        except git.exc.GitCommandError as e:
            raise RepositoryError(f"Failed to checkout {ref}: {e}") from e

    def get_commit_sha(self, ref: Optional[str] = None) -> str:
        """
        Get commit SHA for a reference.

        Args:
            ref: Reference (defaults to current HEAD)

        Returns:
            Commit SHA string

        Raises:
            RepositoryError: If operation fails
        """
        if not self.repo:
            raise RepositoryError("Repository not initialized. Call clone() first.")

        try:
            if ref:
                commit = self.repo.commit(ref)
            else:
                commit = self.repo.head.commit
            return commit.hexsha
        except (git.exc.GitCommandError, ValueError) as e:
            raise RepositoryError(f"Failed to get commit SHA: {e}") from e

    def get_current_branch(self) -> Optional[str]:
        """
        Get current branch name.

        Returns:
            Branch name or None if in detached HEAD state
        """
        if not self.repo:
            return None

        try:
            return self.repo.active_branch.name
        except TypeError:
            # Detached HEAD state
            return None

    def is_dirty(self) -> bool:
        """
        Check if repository has uncommitted changes.

        Returns:
            True if there are uncommitted changes
        """
        if not self.repo:
            return False
        return self.repo.is_dirty()

    def ensure_repo(self, ref: Optional[str] = None) -> git.Repo:
        """
        Ensure repository is cloned and optionally checkout a reference.

        Args:
            ref: Optional reference to checkout

        Returns:
            git.Repo object
        """
        if not self.local_path.exists():
            self.clone()
        elif not self.repo:
            self.repo = git.Repo(self.local_path)

        # Fetch latest changes
        self.fetch()

        if ref:
            self.checkout(ref)

        return self.repo

    def clean(self, force: bool = False) -> None:
        """
        Clean working directory.

        Args:
            force: Force clean even with untracked files
        """
        if not self.repo:
            raise RepositoryError("Repository not initialized. Call clone() first.")

        self.logger.info("Cleaning repository...")
        try:
            self.repo.git.clean("-fd" if force else "-f")
        except git.exc.GitCommandError as e:
            raise RepositoryError(f"Failed to clean repository: {e}") from e
