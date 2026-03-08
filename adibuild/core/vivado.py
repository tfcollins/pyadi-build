"""Vivado download and installation helpers."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests

from adibuild.core.toolchain import ToolchainError, ToolchainInfo
from adibuild.utils.logger import get_logger


@dataclass(frozen=True)
class VivadoRelease:
    """Official AMD Vivado Linux installer metadata."""

    version: str
    installer_version: str
    install_version: str
    filename: str
    download_url: str
    digests_url: str | None
    edition: str = "Vivado ML Standard"


@dataclass(frozen=True)
class VivadoCredentials:
    """Credentials used for AMD account authentication."""

    username: str
    password: str

    @classmethod
    def from_env(cls) -> VivadoCredentials | None:
        """Load credentials from environment variables."""
        username = os.environ.get("AMD_USERNAME")
        password = os.environ.get("AMD_PASSWORD")
        if not username or not password:
            return None
        return cls(username=username, password=password)


@dataclass(frozen=True)
class VivadoInstallRequest:
    """Input for a Vivado installation run."""

    version: str
    install_dir: Path = Path("/opt/Xilinx")
    cache_dir: Path | None = None
    extract_dir: Path | None = None
    installer_path: Path | None = None
    config_path: Path | None = None
    edition: str | None = None
    agree_webtalk_terms: bool = True
    credentials: VivadoCredentials | None = None


@dataclass(frozen=True)
class VivadoInstallResult:
    """Result of a Vivado install workflow."""

    release: VivadoRelease
    installer_path: Path
    extract_dir: Path
    toolchain: ToolchainInfo


class VivadoDownloadError(ToolchainError):
    """Raised when the installer binary cannot be downloaded."""


class VivadoAuthRequiredError(VivadoDownloadError):
    """Raised when AMD authentication is required for download."""


class VivadoInstallError(ToolchainError):
    """Raised when the installer client fails."""


SUPPORTED_RELEASES = {
    "2023.2": VivadoRelease(
        version="2023.2",
        installer_version="2023.2",
        install_version="2023.2",
        filename="FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin"
        ),
        digests_url=(
            "https://www.xilinx.com/content/dam/xilinx/support/download/2023-2/"
            "vivado/FPGAs_AdaptiveSoCs_Unified_2023.2_1013_2256_Lin64.bin.digests"
        ),
    ),
    "2025.1": VivadoRelease(
        version="2025.1",
        installer_version="2025.1.1",
        install_version="2025.1",
        filename="FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin"
        ),
        digests_url=(
            "https://download.amd.com/opendownload/installer/2025.1.1_0912_2/"
            "FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin.digests"
        ),
    ),
    "2025.1.1": VivadoRelease(
        version="2025.1",
        installer_version="2025.1.1",
        install_version="2025.1",
        filename="FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin",
        download_url=(
            "https://account.amd.com/en/forms/downloads/xef.html"
            "?filename=FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin"
        ),
        digests_url=(
            "https://download.amd.com/opendownload/installer/2025.1.1_0912_2/"
            "FPGAs_AdaptiveSoCs_Unified_SDI_2025.1.1_0912_0129_Lin64.bin.digests"
        ),
    ),
}

DEFAULT_BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-User": "?1",
    "Sec-Fetch-Dest": "document",
}


class RequestsDownloadStrategy:
    """Best-effort direct download via HTTP session."""

    def __init__(
        self,
        session: requests.Session | None = None,
        max_attempts: int = 3,
        backoff_seconds: int = 10,
    ):
        self.session = session or requests.Session()
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds
        self.logger = get_logger("adibuild.vivado.http")
        self._apply_browser_headers()

    def download(self, release: VivadoRelease, destination: Path) -> Path:
        """Download the installer or fail if the endpoint requires login."""
        last_error: tuple[str, str, Exception] | None = None
        for attempt in range(1, self.max_attempts + 1):
            self.logger.info(
                "Starting direct AMD download request "
                f"(attempt {attempt}/{self.max_attempts}) to {release.download_url}"
            )
            try:
                return self._download_once(release, destination)
            except _RetryableDownloadError as exc:
                last_error = (exc.stage, exc.message, exc.original_exc)
                if destination.exists():
                    destination.unlink(missing_ok=True)

                if attempt == self.max_attempts:
                    raise VivadoDownloadError(
                        f"Vivado download failed at stage={exc.stage} after "
                        f"{self.max_attempts} attempts: {exc.message}"
                    ) from exc.original_exc

                delay = self.backoff_seconds * attempt
                self.logger.warning(
                    "Direct AMD download attempt "
                    f"{attempt}/{self.max_attempts} failed at stage={exc.stage}: "
                    f"{exc.message}. Retrying in {delay}s"
                )
                time.sleep(delay)

        stage, message, original_exc = last_error or (
            "unknown",
            "download failed",
            RuntimeError("download failed"),
        )
        raise VivadoDownloadError(
            f"Vivado download failed at stage={stage}: {message}"
        ) from original_exc

    def _download_once(self, release: VivadoRelease, destination: Path) -> Path:
        """Perform a single direct download attempt."""
        self._bootstrap_amd_session(release)
        try:
            response = self.session.get(
                release.download_url,
                stream=True,
                allow_redirects=True,
                timeout=300,
            )
        except requests.Timeout as exc:
            raise _RetryableDownloadError(
                stage="initial-http-request",
                message=f"timed out while requesting {release.download_url}",
                original_exc=exc,
            ) from exc
        except requests.RequestException as exc:
            raise _RetryableDownloadError(
                stage="initial-http-request",
                message=f"request to {release.download_url} failed with {exc}",
                original_exc=exc,
            ) from exc

        final_url = response.url.lower()
        content_type = response.headers.get("content-type", "").lower()
        disposition = response.headers.get("content-disposition", "")
        content_length = response.headers.get("content-length", "unknown")
        self.logger.info(
            "AMD download response: "
            f"status={response.status_code}, final_url={response.url}, "
            f"content_type={content_type or 'unknown'}, content_length={content_length}"
        )

        if response.status_code >= 400:
            response.close()
            raise VivadoDownloadError(
                f"AMD download endpoint returned HTTP {response.status_code}"
            )

        is_binary = "application/octet-stream" in content_type or disposition
        looks_like_login = any(
            marker in final_url
            for marker in ("login", "signin", "account.amd.com", "oauth", "saml")
        )
        if looks_like_login and not is_binary:
            response.close()
            raise VivadoAuthRequiredError(
                "AMD requires an authenticated download session for this installer"
            )
        if not is_binary:
            response.close()
            raise VivadoDownloadError(
                f"Unexpected non-binary response from AMD download endpoint: {final_url}"
            )

        destination.parent.mkdir(parents=True, exist_ok=True)
        downloaded_bytes = 0
        progress_interval = 100 * 1024 * 1024
        next_progress_log = progress_interval
        try:
            with destination.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        handle.write(chunk)
                        downloaded_bytes += len(chunk)
                        if downloaded_bytes >= next_progress_log:
                            self.logger.info(
                                "Direct AMD download progress: "
                                f"{downloaded_bytes / (1024 * 1024):.1f} MiB written "
                                f"to {destination}"
                            )
                            next_progress_log += progress_interval
        except requests.Timeout as exc:
            response.close()
            raise _RetryableDownloadError(
                stage="download-stream",
                message=(
                    f"timed out while streaming {response.url} after "
                    f"{downloaded_bytes / (1024 * 1024):.1f} MiB"
                ),
                original_exc=exc,
            ) from exc
        except requests.RequestException as exc:
            response.close()
            raise _RetryableDownloadError(
                stage="download-stream",
                message=(
                    f"streaming {response.url} failed after "
                    f"{downloaded_bytes / (1024 * 1024):.1f} MiB with {exc}"
                ),
                original_exc=exc,
            ) from exc
        response.close()
        self.logger.info(
            "Completed direct AMD download: "
            f"{downloaded_bytes / (1024 * 1024):.1f} MiB saved to {destination}"
        )
        return destination

    def _apply_browser_headers(self) -> None:
        """Apply browser-like defaults so AMD does not treat requests as a bare bot."""
        for key, value in DEFAULT_BROWSER_HEADERS.items():
            current = self.session.headers.get(key)
            if (
                key == "User-Agent"
                and current
                and not current.startswith("python-requests/")
            ):
                continue
            self.session.headers[key] = value

    def _bootstrap_amd_session(self, release: VivadoRelease) -> None:
        """Prime AMD/F5 session cookies before hitting auth-gated download URLs."""
        parsed = urlparse(release.download_url)
        if parsed.netloc.lower() != "account.amd.com":
            return

        bootstrap_url = f"{parsed.scheme}://{parsed.netloc}/"
        self.logger.info(f"Bootstrapping AMD auth gateway at {bootstrap_url}")
        try:
            response = self.session.get(
                bootstrap_url,
                allow_redirects=False,
                timeout=30,
            )
        except requests.RequestException as exc:
            self.logger.warning(
                f"AMD auth gateway bootstrap failed for {bootstrap_url}: {exc}"
            )
            return

        location = response.headers.get("location")
        self.logger.info(
            "AMD auth gateway bootstrap response: "
            f"status={response.status_code}, location={location or 'none'}"
        )
        response.close()


@dataclass(frozen=True)
class _RetryableDownloadError(Exception):
    """Internal exception for retryable AMD download failures."""

    stage: str
    message: str
    original_exc: Exception


class PlaywrightDownloadStrategy:
    """Optional browser-driven fallback for authenticated downloads."""

    EMAIL_SELECTORS = (
        "input[type='email']",
        "input[name='email']",
        "input[name='username']",
        "input[name='loginfmt']",
        "#i0116",
    )
    PASSWORD_SELECTORS = (
        "input[type='password']",
        "input[name='password']",
        "#i0118",
    )
    SUBMIT_SELECTORS = (
        "button[type='submit']",
        "input[type='submit']",
        "#idSIButton9",
    )

    def __init__(self):
        try:
            from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise VivadoDownloadError(
                "Browser download fallback requires the 'vivado-browser' extra"
            ) from exc

        self._playwright_timeout_error = PlaywrightTimeoutError
        self._sync_playwright = sync_playwright
        self.logger = get_logger("adibuild.vivado.browser")

    def download(
        self,
        release: VivadoRelease,
        destination: Path,
        credentials: VivadoCredentials,
    ) -> Path:
        """Login to AMD and download the installer."""
        destination.parent.mkdir(parents=True, exist_ok=True)
        self.logger.info(
            f"Starting browser-authenticated AMD download for {release.filename}"
        )

        with self._sync_playwright() as playwright:
            self.logger.info("Launching Chromium for AMD download")
            browser = playwright.chromium.launch(**self._launch_options())
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            auth_url = self._auth_bootstrap_url(release)
            self.logger.info(f"Opening AMD login page {auth_url}")
            self._goto_with_retry(
                page,
                auth_url,
                "browser-login-navigation",
                settle_dom=True,
            )
            self._login_if_needed(page, credentials)

            self.logger.info(
                "Exporting authenticated browser session into requests for "
                "byte-level download progress tracking"
            )
            session = self._session_from_browser_context(context, page)
            try:
                self.logger.info(
                    "Starting authenticated HTTP installer download "
                    f"for {release.download_url}"
                )
                target = RequestsDownloadStrategy(session=session).download(
                    release, destination
                )
                context.close()
                browser.close()
                return target
            except VivadoDownloadError as exc:
                self.logger.warning(
                    "Authenticated HTTP handoff failed after browser login: "
                    f"{exc}. Falling back to Playwright-managed download "
                    "without byte-level progress"
                )

            try:
                self.logger.info(
                    "Waiting for browser-authenticated AMD installer download to start"
                )
                with page.expect_download(timeout=180000) as download_info:
                    self._goto_with_retry(
                        page,
                        release.download_url,
                        "browser-download-navigation",
                        settle_dom=False,
                    )
                download = download_info.value
            except self._playwright_timeout_error as exc:
                raise VivadoDownloadError(
                    "Vivado download failed at stage=browser-download-wait: "
                    "timed out waiting for the authenticated download"
                ) from exc

            suggested_name = download.suggested_filename or release.filename
            target = destination
            if destination.name != suggested_name:
                target = destination.parent / suggested_name

            download.save_as(str(target))
            self.logger.info(f"Saved browser-authenticated AMD download to {target}")
            context.close()
            browser.close()
            return target

    @staticmethod
    def _auth_bootstrap_url(release: VivadoRelease) -> str:
        """Choose a stable landing page for browser-based authentication."""
        download_url = release.download_url.lower()
        if "account.amd.com" in download_url or "xilinx.com/member/forms" in download_url:
            return "https://account.amd.com/"

        parsed = urlparse(release.download_url)
        return f"{parsed.scheme}://{parsed.netloc}/"

    @staticmethod
    def _launch_options() -> dict[str, object]:
        """Return browser launch options that work in containerized environments."""
        options: dict[str, object] = {
            "headless": True,
            "args": ["--disable-http2"],
        }
        geteuid = getattr(os, "geteuid", None)
        if geteuid is not None and geteuid() == 0:
            options["args"].append("--no-sandbox")
        return options

    def _login_if_needed(
        self, page, credentials: VivadoCredentials  # pragma: no cover - mocked in tests
    ) -> None:
        """Fill common AMD/Microsoft-style login forms."""
        try:
            email_locator = self._first_visible(page, self.EMAIL_SELECTORS)
            if email_locator:
                self.logger.info("Detected AMD login email prompt; submitting username")
                email_locator.fill(credentials.username)
                self._click_first(page, self.SUBMIT_SELECTORS)
                page.wait_for_load_state("domcontentloaded", timeout=30000)

            password_locator = self._first_visible(page, self.PASSWORD_SELECTORS)
            if password_locator:
                self.logger.info(
                    "Detected AMD login password prompt; submitting password"
                )
                password_locator.fill(credentials.password)
                self._click_first(page, self.SUBMIT_SELECTORS)
                page.wait_for_load_state("domcontentloaded", timeout=30000)
            else:
                self.logger.info("No browser login form detected after auth bootstrap")
        except Exception as exc:  # pragma: no cover - integration-only timing
            raise VivadoDownloadError(
                f"Vivado download failed at stage=browser-login-submit: {exc}"
            ) from exc

    def _goto_with_retry(
        self,
        page,
        url: str,
        stage: str,
        settle_dom: bool = False,
    ) -> None:
        """Navigate with retries for flaky AMD/Xilinx endpoints."""
        last_exc = None
        for attempt in range(1, 4):
            try:
                self.logger.info(
                    f"Browser navigation stage={stage} attempt {attempt}/3 to {url}"
                )
                page.goto(url, wait_until="commit", timeout=180000)
                if settle_dom:
                    try:
                        page.wait_for_load_state("domcontentloaded", timeout=10000)
                    except Exception as exc:  # pragma: no cover - integration-only timing
                        self.logger.info(
                            f"Browser navigation stage={stage} committed but did not reach "
                            f"domcontentloaded within 10s: {exc}"
                        )
                return
            except Exception as exc:  # pragma: no cover - exercised in integration
                last_exc = exc
                self.logger.warning(
                    f"Browser navigation failed at stage={stage} attempt {attempt}/3: {exc}"
                )
                if attempt < 3:
                    page.wait_for_timeout(3000)

        raise VivadoDownloadError(
            f"Vivado download failed at stage={stage}: browser navigation to {url} "
            f"failed after 3 attempts with {last_exc}"
        ) from last_exc

    def _session_from_browser_context(self, context, page) -> requests.Session:
        """Build a requests session from authenticated browser cookies."""
        session = requests.Session()
        for cookie in context.cookies():
            session.cookies.set(
                cookie["name"],
                cookie["value"],
                domain=cookie.get("domain"),
                path=cookie.get("path", "/"),
            )

        try:
            user_agent = page.evaluate("() => navigator.userAgent")
        except Exception:
            user_agent = None
        if user_agent:
            session.headers.update({"User-Agent": user_agent})
        return session

    @staticmethod
    def _first_visible(page, selectors):
        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() and locator.is_visible():
                return locator
        return None

    @staticmethod
    def _click_first(page, selectors):
        locator = PlaywrightDownloadStrategy._first_visible(page, selectors)
        if locator:
            locator.click()


class VivadoInstaller:
    """Download, verify, and install AMD Vivado on Linux."""

    AGREEMENTS = ("XilinxEULA", "3rdPartyEULA", "WebTalkTerms")
    BROWSER_AUTH_HOST_MARKERS = ("account.amd.com", "www.xilinx.com/member/forms")

    def __init__(
        self,
        cache_dir: Path | None = None,
        release_catalog: dict[str, VivadoRelease] | None = None,
    ):
        self.cache_dir = cache_dir or Path.home() / ".adibuild" / "toolchains" / "vivado"
        self.release_catalog = release_catalog or SUPPORTED_RELEASES
        self.logger = get_logger("adibuild.vivado")

    def list_supported_releases(self) -> list[VivadoRelease]:
        """Return unique supported releases."""
        seen = set()
        releases = []
        for release in self.release_catalog.values():
            if release.version not in seen:
                releases.append(release)
                seen.add(release.version)
        return sorted(releases, key=lambda item: item.version)

    def resolve_release(self, version: str) -> VivadoRelease:
        """Resolve a user-requested version to installer metadata."""
        if version not in self.release_catalog:
            supported = ", ".join(rel.version for rel in self.list_supported_releases())
            raise VivadoDownloadError(
                f"Unsupported Vivado version '{version}'. Supported versions: {supported}"
            )
        release = self.release_catalog[version]
        self.logger.info(
            "Resolved Vivado release "
            f"{version} -> installer {release.installer_version} "
            f"({release.filename})"
        )
        return release

    def download_installer(
        self,
        version: str,
        cache_dir: Path | None = None,
        credentials: VivadoCredentials | None = None,
    ) -> Path:
        """Download the self-extracting Linux web installer."""
        release = self.resolve_release(version)
        cache_root = cache_dir or self.cache_dir / "installers"
        installer_path = cache_root / release.filename

        if installer_path.exists():
            self.logger.info(f"Using cached Vivado installer at {installer_path}")
            self.verify_installer(release, installer_path)
            return installer_path

        self.logger.info(
            f"Downloading Vivado {release.version} installer to {installer_path}"
        )
        if self._prefer_browser_download(release, credentials):
            self.logger.info(
                "Skipping direct HTTP download because this AMD endpoint is "
                "authentication-gated and credentials are available"
            )
            installer_path = PlaywrightDownloadStrategy().download(
                release, installer_path, credentials
            )
            self.verify_installer(release, installer_path)
            installer_path.chmod(installer_path.stat().st_mode | 0o111)
            self.logger.info(f"Vivado installer ready at {installer_path}")
            return installer_path

        try:
            RequestsDownloadStrategy().download(release, installer_path)
        except VivadoAuthRequiredError:
            if not credentials:
                raise

            self.logger.info("Falling back to authenticated browser download")
            installer_path = PlaywrightDownloadStrategy().download(
                release, installer_path, credentials
            )

        self.verify_installer(release, installer_path)
        installer_path.chmod(installer_path.stat().st_mode | 0o111)
        self.logger.info(f"Vivado installer ready at {installer_path}")
        return installer_path

    def _prefer_browser_download(
        self,
        release: VivadoRelease,
        credentials: VivadoCredentials | None,
    ) -> bool:
        """Decide whether to skip direct HTTP download and use browser auth first."""
        if not credentials:
            return False

        download_url = release.download_url.lower()
        return any(marker in download_url for marker in self.BROWSER_AUTH_HOST_MARKERS)

    def verify_installer(self, release: VivadoRelease, installer_path: Path) -> None:
        """Verify the installer against AMD-published digests when available."""
        if os.environ.get("ADIBUILD_VIVADO_SKIP_VERIFY", "").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }:
            self.logger.warning(
                f"Skipping Vivado installer verification for {installer_path} "
                "because ADIBUILD_VIVADO_SKIP_VERIFY is set"
            )
            return

        if not installer_path.exists():
            raise VivadoDownloadError(f"Installer not found: {installer_path}")

        if not release.digests_url:
            self.logger.info(
                f"No digest URL published for {release.filename}; skipping verification"
            )
            return

        digest_map = self._fetch_digest_map(release)
        sha256 = digest_map.get("sha256")
        if not sha256:
            self.logger.info(
                f"No SHA256 digest found for {release.filename}; skipping verification"
            )
            return

        actual_sha256 = self._hash_file(installer_path, "sha256")
        if actual_sha256 != sha256:
            raise VivadoDownloadError(
                f"Digest mismatch for {installer_path.name}: expected {sha256}, "
                f"got {actual_sha256}"
            )
        self.logger.info(f"Verified SHA256 for {installer_path.name}")

    def install(self, request: VivadoInstallRequest) -> VivadoInstallResult:
        """Install a supported Vivado release via the web installer client."""
        release = self.resolve_release(request.version)
        credentials = request.credentials or VivadoCredentials.from_env()
        self.logger.info(
            f"Starting Vivado install for {release.version} into {request.install_dir}"
        )
        installer_path = request.installer_path
        if installer_path is None:
            installer_path = self.download_installer(
                release.version,
                cache_dir=request.cache_dir,
                credentials=credentials,
            )
        else:
            self.logger.info(f"Using caller-provided installer at {installer_path}")
            self.verify_installer(release, installer_path)
            self._ensure_executable(installer_path)

        extract_dir = self.extract_web_installer(
            release=release,
            installer_path=installer_path,
            extract_dir=request.extract_dir,
        )
        xsetup = self._find_xsetup(extract_dir)

        if request.config_path is None and credentials is None:
            raise VivadoInstallError(
                "Vivado web installation requires AMD_USERNAME/AMD_PASSWORD "
                "or explicit credentials"
            )

        if credentials is not None:
            self.logger.info("Generating AMD installer authentication token")
            self.acquire_auth_token(xsetup, credentials)
        else:
            self.logger.info(
                "Skipping token generation because a config file was provided"
            )

        self.logger.info(
            f"Running Vivado batch installer from {xsetup.parent} "
            f"to target root {request.install_dir}"
        )
        self.run_install(
            release=release,
            xsetup=xsetup,
            install_dir=request.install_dir,
            config_path=request.config_path,
            edition=request.edition or release.edition,
            agree_webtalk_terms=request.agree_webtalk_terms,
        )

        toolchain = self.status(release.version, request.install_dir)
        if toolchain is None:
            raise VivadoInstallError(
                f"Vivado {release.install_version} was installed but could not be detected"
            )
        self.logger.info(
            f"Detected installed Vivado {toolchain.version} at {toolchain.path}"
        )

        return VivadoInstallResult(
            release=release,
            installer_path=installer_path,
            extract_dir=extract_dir,
            toolchain=toolchain,
        )

    def _ensure_executable(self, path: Path) -> None:
        """Ensure an installer binary is executable without failing on read-only mounts."""
        if os.access(path, os.X_OK):
            return

        try:
            path.chmod(path.stat().st_mode | 0o111)
        except OSError as exc:
            if os.access(path, os.X_OK):
                return
            raise VivadoInstallError(
                f"Could not mark installer executable: {path}: {exc}"
            ) from exc

    def status(
        self,
        version: str | None = None,
        install_dir: Path | None = None,
    ) -> ToolchainInfo | None:
        """Detect an installed Vivado release, optionally scoped to a root directory."""
        from adibuild.core.toolchain import VivadoToolchain

        search_paths = None
        if install_dir and version:
            release = self.resolve_release(version)
            search_paths = [
                install_dir / "Vivado" / release.install_version,
                install_dir / "Vitis" / release.install_version,
                install_dir / release.install_version / "Vivado",
                install_dir / release.install_version / "Vitis",
            ]
        elif install_dir:
            search_paths = []
            for product in ("Vivado", "Vitis"):
                product_root = install_dir / product
                if product_root.exists():
                    search_paths.extend(
                        path for path in product_root.iterdir() if path.is_dir()
                    )
            for version_root in (install_dir.iterdir() if install_dir.exists() else []):
                if not version_root.is_dir():
                    continue
                search_paths.extend(
                    candidate
                    for candidate in (
                        version_root / "Vivado",
                        version_root / "Vitis",
                    )
                    if candidate.exists()
                )

        if search_paths is not None:
            self.logger.info(
                "Checking Vivado installation status in: "
                + ", ".join(str(path) for path in search_paths)
            )
        elif version:
            self.logger.info(f"Checking Vivado installation status for version {version}")
        else:
            self.logger.info(
                "Checking Vivado installation status in default search paths"
            )

        toolchain = VivadoToolchain(
            search_paths=search_paths,
            preferred_version=version,
            strict_version=bool(version),
        )
        return toolchain.detect()

    def extract_web_installer(
        self,
        release: VivadoRelease,
        installer_path: Path,
        extract_dir: Path | None = None,
    ) -> Path:
        """Extract the batch client out of the self-extracting installer."""
        target_dir = extract_dir or self.cache_dir / "extracted" / release.version
        target_dir.mkdir(parents=True, exist_ok=True)

        xsetup = self._find_xsetup(target_dir, required=False)
        if xsetup is not None:
            self.logger.info(f"Using cached extracted installer client at {target_dir}")
            return target_dir

        self.logger.info(f"Extracting Vivado installer into {target_dir}")
        cmd = [
            str(installer_path),
            "--keep",
            "--noexec",
            "--target",
            str(target_dir),
        ]
        self._run_command(cmd, check=True)
        self.logger.info(f"Extracted Vivado installer into {target_dir}")
        return target_dir

    def acquire_auth_token(
        self, xsetup: Path, credentials: VivadoCredentials
    ) -> subprocess.CompletedProcess:
        """Generate a short-lived authentication token for the web installer."""
        input_data = f"{credentials.username}\n{credentials.password}\n"
        return self._run_command(
            [str(xsetup), "-b", "AuthTokenGen"],
            cwd=xsetup.parent,
            input_data=input_data,
            check=True,
            redact_output=True,
        )

    def run_install(
        self,
        release: VivadoRelease,
        xsetup: Path,
        install_dir: Path,
        config_path: Path | None,
        edition: str,
        agree_webtalk_terms: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run the extracted installer client in batch mode."""
        agreements = list(self.AGREEMENTS[:2])
        if agree_webtalk_terms:
            agreements.append(self.AGREEMENTS[2])

        cmd = [
            str(xsetup),
            "-b",
            "Install",
            "-a",
            ",".join(agreements),
        ]
        if config_path:
            cmd.extend(["-c", str(config_path)])
        else:
            cmd.extend(["--edition", edition, "--location", str(install_dir)])

        install_dir.mkdir(parents=True, exist_ok=True)
        return self._run_command(cmd, cwd=xsetup.parent, check=True)

    def _fetch_digest_map(self, release: VivadoRelease) -> dict[str, str]:
        self.logger.info(f"Fetching official digests from {release.digests_url}")
        response = requests.get(release.digests_url, timeout=60)
        response.raise_for_status()

        digest_map = {}
        algo_order = ("md5", "sha1", "sha256", "sha512")
        for line in response.text.splitlines():
            match = re.match(r"([a-fA-F0-9]{32,128})\s+\*?(.+)$", line.strip())
            if not match:
                continue
            digest = match.group(1).lower()
            filename = Path(match.group(2)).name
            if filename != release.filename:
                continue

            if len(digest) == 32:
                digest_map[algo_order[0]] = digest
            elif len(digest) == 40:
                digest_map[algo_order[1]] = digest
            elif len(digest) == 64:
                digest_map[algo_order[2]] = digest
            elif len(digest) == 128:
                digest_map[algo_order[3]] = digest

        return digest_map

    @staticmethod
    def _hash_file(path: Path, algorithm: str) -> str:
        hasher = hashlib.new(algorithm)
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def _find_xsetup(root: Path, required: bool = True) -> Path | None:
        direct = root / "xsetup"
        if direct.exists():
            return direct

        candidates = list(root.rglob("xsetup"))
        if candidates:
            return candidates[0]

        if required:
            raise VivadoInstallError(f"Could not find xsetup under {root}")
        return None

    def _run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        input_data: str | None = None,
        check: bool = False,
        redact_output: bool = False,
    ) -> subprocess.CompletedProcess:
        self.logger.info(f"Running command: {' '.join(shlex_quote(arg) for arg in cmd)}")
        result = subprocess.run(
            cmd,
            cwd=cwd,
            input=input_data,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 and check:
            stdout = result.stdout
            stderr = result.stderr
            if redact_output:
                stdout = "<redacted>"
                stderr = "<redacted>"
            raise VivadoInstallError(
                f"Command failed with exit code {result.returncode}: "
                f"{' '.join(shlex_quote(arg) for arg in cmd)}\n"
                f"stdout: {stdout}\n"
                f"stderr: {stderr}"
            )
        if redact_output:
            if result.stdout.strip() or result.stderr.strip():
                self.logger.info("Command output redacted")
            return result

        if result.stdout.strip():
            self.logger.info(f"Command stdout:\n{result.stdout.strip()}")
        if result.stderr.strip():
            self.logger.info(f"Command stderr:\n{result.stderr.strip()}")
        return result


def shlex_quote(value: str) -> str:
    """Quote command arguments for logs without importing shlex at module load."""
    import shlex

    return shlex.quote(value)
