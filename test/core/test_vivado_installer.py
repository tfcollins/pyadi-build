"""Tests for Vivado installer helpers."""

from pathlib import Path

import pytest
import requests

from adibuild.core.toolchain import ToolchainInfo
from adibuild.core.vivado import (
    DEFAULT_BROWSER_HEADERS,
    SUPPORTED_RELEASES,
    PlaywrightDownloadStrategy,
    RequestsDownloadStrategy,
    VivadoAuthRequiredError,
    VivadoCredentials,
    VivadoDownloadError,
    VivadoInstaller,
    VivadoInstallError,
    VivadoInstallRequest,
)


def test_list_supported_releases_deduplicates_alias_versions():
    installer = VivadoInstaller()

    versions = [release.version for release in installer.list_supported_releases()]

    assert versions == ["2023.2", "2025.1"]


def test_resolve_release_supports_2025_1_alias():
    installer = VivadoInstaller()

    release = installer.resolve_release("2025.1.1")

    assert release.version == "2025.1"
    assert release.install_version == "2025.1"


def test_verify_installer_uses_sha256_digest(tmp_path, mocker):
    installer = VivadoInstaller()
    release = SUPPORTED_RELEASES["2023.2"]
    installer_path = tmp_path / release.filename
    installer_path.write_bytes(b"installer-data")
    mocker.patch.object(
        installer,
        "_fetch_digest_map",
        return_value={"sha256": installer._hash_file(installer_path, "sha256")},
    )

    installer.verify_installer(release, installer_path)


def test_verify_installer_raises_on_digest_mismatch(tmp_path, mocker):
    installer = VivadoInstaller()
    release = SUPPORTED_RELEASES["2023.2"]
    installer_path = tmp_path / release.filename
    installer_path.write_bytes(b"installer-data")
    mocker.patch.object(
        installer,
        "_fetch_digest_map",
        return_value={"sha256": "deadbeef" * 8},
    )

    with pytest.raises(VivadoDownloadError, match="Digest mismatch"):
        installer.verify_installer(release, installer_path)


def test_download_installer_uses_cache_when_present(tmp_path, mocker):
    installer = VivadoInstaller(cache_dir=tmp_path)
    release = SUPPORTED_RELEASES["2023.2"]
    cached = tmp_path / "installers" / release.filename
    cached.parent.mkdir(parents=True)
    cached.write_bytes(b"cached-installer")

    verify = mocker.patch.object(installer, "verify_installer")
    request_download = mocker.patch(
        "adibuild.core.vivado.RequestsDownloadStrategy.download"
    )

    result = installer.download_installer("2023.2")

    assert result == cached
    verify.assert_called_once_with(release, cached)
    request_download.assert_not_called()


def test_download_installer_falls_back_to_browser_with_credentials(tmp_path, mocker):
    installer = VivadoInstaller(cache_dir=tmp_path)
    browser_file = tmp_path / "browser-download.bin"
    browser_file.write_bytes(b"browser-download")

    mocker.patch.object(
        installer,
        "verify_installer",
        return_value=None,
    )
    mocker.patch(
        "adibuild.core.vivado.RequestsDownloadStrategy.download",
        side_effect=VivadoAuthRequiredError("auth required"),
    )
    browser_strategy = mocker.Mock()
    browser_strategy.download.return_value = browser_file
    mocker.patch(
        "adibuild.core.vivado.PlaywrightDownloadStrategy",
        return_value=browser_strategy,
    )

    result = installer.download_installer(
        "2023.2",
        credentials=VivadoCredentials(username="user", password="pass"),
    )

    assert result == browser_file
    browser_strategy.download.assert_called_once()


def test_download_installer_prefers_browser_for_auth_gated_urls(tmp_path, mocker):
    installer = VivadoInstaller(cache_dir=tmp_path)
    browser_file = tmp_path / "browser-download.bin"
    browser_file.write_bytes(b"browser-download")

    mocker.patch.object(installer, "verify_installer", return_value=None)
    direct_download = mocker.patch(
        "adibuild.core.vivado.RequestsDownloadStrategy.download"
    )
    browser_strategy = mocker.Mock()
    browser_strategy.download.return_value = browser_file
    mocker.patch(
        "adibuild.core.vivado.PlaywrightDownloadStrategy",
        return_value=browser_strategy,
    )

    result = installer.download_installer(
        "2023.2",
        credentials=VivadoCredentials(username="user", password="pass"),
    )

    assert result == browser_file
    direct_download.assert_not_called()
    browser_strategy.download.assert_called_once()


def test_direct_download_timeout_includes_stage_and_url(mocker, tmp_path):
    session = mocker.Mock()
    session.headers = {}
    session.get.side_effect = requests.Timeout("boom")
    sleep = mocker.patch("time.sleep")
    strategy = RequestsDownloadStrategy(
        session=session,
        max_attempts=2,
        backoff_seconds=0,
    )
    mocker.patch.object(strategy, "_bootstrap_amd_session")
    release = SUPPORTED_RELEASES["2025.1"]

    with pytest.raises(
        VivadoDownloadError,
        match="stage=initial-http-request after 2 attempts",
    ):
        strategy.download(release, tmp_path / release.filename)
    assert session.get.call_count == 2
    sleep.assert_called_once_with(0)


def test_direct_download_retries_timeout_then_succeeds(mocker, tmp_path):
    response = mocker.Mock()
    response.url = "https://download.amd.com/example.bin"
    response.headers = {
        "content-type": "application/octet-stream",
        "content-length": "4",
    }
    response.status_code = 200
    response.iter_content.return_value = [b"test"]

    session = mocker.Mock()
    session.headers = {}
    session.get.side_effect = [requests.Timeout("boom"), response]
    sleep = mocker.patch("time.sleep")
    strategy = RequestsDownloadStrategy(
        session=session,
        max_attempts=2,
        backoff_seconds=0,
    )
    mocker.patch.object(strategy, "_bootstrap_amd_session")
    release = SUPPORTED_RELEASES["2023.2"]
    destination = tmp_path / release.filename

    result = strategy.download(release, destination)

    assert result == destination
    assert destination.read_bytes() == b"test"
    assert session.get.call_count == 2
    sleep.assert_called_once_with(0)


def test_requests_download_strategy_applies_browser_headers():
    session = requests.Session()

    strategy = RequestsDownloadStrategy(session=session)

    for key, value in DEFAULT_BROWSER_HEADERS.items():
        assert strategy.session.headers[key] == value


def test_requests_download_strategy_preserves_existing_user_agent():
    session = requests.Session()
    session.headers["User-Agent"] = "custom-agent"

    strategy = RequestsDownloadStrategy(session=session)

    assert strategy.session.headers["User-Agent"] == "custom-agent"


def test_direct_download_bootstraps_account_amd_session_before_download(mocker, tmp_path):
    bootstrap_response = mocker.Mock()
    bootstrap_response.status_code = 302
    bootstrap_response.headers = {"location": "/my.policy"}
    bootstrap_response.close.return_value = None

    response = mocker.Mock()
    response.url = "https://download.amd.com/example.bin"
    response.headers = {
        "content-type": "application/octet-stream",
        "content-length": "4",
    }
    response.status_code = 200
    response.iter_content.return_value = [b"test"]
    response.close.return_value = None

    session = mocker.Mock(spec=requests.Session)
    session.headers = {}
    session.get.side_effect = [bootstrap_response, response]
    strategy = RequestsDownloadStrategy(
        session=session,
        max_attempts=1,
        backoff_seconds=0,
    )
    release = SUPPORTED_RELEASES["2023.2"]
    destination = tmp_path / release.filename

    result = strategy.download(release, destination)

    assert result == destination
    assert session.get.call_count == 2
    first_call = session.get.call_args_list[0]
    second_call = session.get.call_args_list[1]
    assert first_call.args[0] == "https://account.amd.com/"
    assert first_call.kwargs["allow_redirects"] is False
    assert second_call.args[0] == release.download_url


def test_resolve_release_rejects_unsupported_version():
    installer = VivadoInstaller()

    with pytest.raises(VivadoDownloadError):
        installer.resolve_release("2024.3")


def test_install_runs_download_extract_token_and_install(tmp_path, mocker):
    installer = VivadoInstaller(cache_dir=tmp_path)
    release = SUPPORTED_RELEASES["2023.2"]
    installer_bin = tmp_path / release.filename
    installer_bin.write_bytes(b"installer")
    extracted = tmp_path / "extract"
    xsetup = extracted / "xsetup"
    toolchain = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vivado/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
        cross_compile_microblaze="microblazeel-xilinx-linux-gnu-",
    )

    mocker.patch.object(installer, "verify_installer")
    download = mocker.patch.object(
        installer,
        "download_installer",
        return_value=installer_bin,
    )
    extract = mocker.patch.object(
        installer, "extract_web_installer", return_value=extracted
    )
    mocker.patch.object(installer, "_find_xsetup", return_value=xsetup)
    token = mocker.patch.object(installer, "acquire_auth_token")
    run_install = mocker.patch.object(installer, "run_install")
    status = mocker.patch.object(installer, "status", return_value=toolchain)

    result = installer.install(
        VivadoInstallRequest(
            version="2023.2",
            install_dir=Path("/opt/Xilinx"),
            credentials=VivadoCredentials(username="user", password="pass"),
        )
    )

    assert result.release == release
    assert result.toolchain == toolchain
    download.assert_called_once()
    extract.assert_called_once_with(
        release=release,
        installer_path=installer_bin,
        extract_dir=None,
    )
    token.assert_called_once_with(
        xsetup, VivadoCredentials(username="user", password="pass")
    )
    run_install.assert_called_once()
    status.assert_called_once_with("2023.2", Path("/opt/Xilinx"))


def test_install_requires_credentials_or_config(tmp_path, mocker):
    installer = VivadoInstaller(cache_dir=tmp_path)
    release = SUPPORTED_RELEASES["2023.2"]
    installer_bin = tmp_path / release.filename
    installer_bin.write_bytes(b"installer")
    mocker.patch.object(installer, "download_installer", return_value=installer_bin)
    mocker.patch.object(
        installer,
        "extract_web_installer",
        return_value=tmp_path / "extract",
    )
    mocker.patch.object(
        installer,
        "_find_xsetup",
        return_value=tmp_path / "extract" / "xsetup",
    )

    with pytest.raises(VivadoInstallError, match="requires AMD_USERNAME/AMD_PASSWORD"):
        installer.install(VivadoInstallRequest(version="2023.2"))


def test_status_uses_scoped_search_paths(tmp_path, mocker):
    info = ToolchainInfo(
        type="vivado",
        version="2023.2",
        path=Path("/opt/Xilinx/Vivado/2023.2"),
        env_vars={},
        cross_compile_arm32="arm-linux-gnueabihf-",
        cross_compile_arm64="aarch64-linux-gnu-",
    )
    detect = mocker.patch(
        "adibuild.core.toolchain.VivadoToolchain.detect",
        return_value=info,
    )

    installer = VivadoInstaller(cache_dir=tmp_path)
    result = installer.status("2023.2", Path("/opt/Xilinx"))

    assert result == info
    detect.assert_called_once()


def test_playwright_launch_options_disable_sandbox_for_root(mocker):
    mocker.patch("os.geteuid", return_value=0)

    options = PlaywrightDownloadStrategy._launch_options()

    assert options["headless"] is True
    assert "--disable-http2" in options["args"]
    assert "--no-sandbox" in options["args"]


def test_playwright_launch_options_disable_http2_for_non_root(mocker):
    mocker.patch("os.geteuid", return_value=1000)

    options = PlaywrightDownloadStrategy._launch_options()

    assert options["headless"] is True
    assert "--disable-http2" in options["args"]
    assert "--disable-blink-features=AutomationControlled" in options["args"]


def test_goto_with_retry_retries_then_succeeds():
    strategy = object.__new__(PlaywrightDownloadStrategy)

    class FakePage:
        def __init__(self):
            self.calls = 0
            self.url = "https://example.com"
            self.title = lambda: "Example"

        def goto(self, url, wait_until, timeout):
            self.calls += 1
            if self.calls < 2:
                raise RuntimeError("net error")

        def wait_for_timeout(self, ms):
            return None

    page = FakePage()
    strategy.logger = type(
        "Logger",
        (),
        {"info": lambda *args, **kwargs: None, "warning": lambda *args, **kwargs: None},
    )()

    strategy._goto_with_retry(page, "https://example.com", "test-stage")

    assert page.calls == 2


def test_goto_with_retry_raises_after_exhausting_attempts():
    strategy = object.__new__(PlaywrightDownloadStrategy)

    class FakePage:
        def __init__(self):
            self.calls = 0
            self.url = "https://example.com"
            self.title = lambda: "Example"

        def goto(self, url, wait_until, timeout):
            self.calls += 1
            raise RuntimeError("net error")

        def wait_for_timeout(self, ms):
            return None

    page = FakePage()
    strategy.logger = type(
        "Logger",
        (),
        {"info": lambda *args, **kwargs: None, "warning": lambda *args, **kwargs: None},
    )()

    with pytest.raises(VivadoDownloadError, match="stage=test-stage"):
        strategy._goto_with_retry(page, "https://example.com", "test-stage")

    assert page.calls == 3


def test_session_from_browser_context_copies_cookies_and_user_agent():
    strategy = object.__new__(PlaywrightDownloadStrategy)

    class FakeContext:
        @staticmethod
        def cookies():
            return [
                {
                    "name": "auth_cookie",
                    "value": "secret",
                    "domain": ".xilinx.com",
                    "path": "/",
                }
            ]

    class FakePage:
        @staticmethod
        def evaluate(script):
            return "test-user-agent"

    session = strategy._session_from_browser_context(FakeContext(), FakePage())

    assert session.headers["User-Agent"] == "test-user-agent"
    assert session.cookies.get("auth_cookie", domain=".xilinx.com", path="/") == "secret"


def test_auth_bootstrap_url_normalizes_legacy_xilinx_downloads():
    bootstrap_url = PlaywrightDownloadStrategy._auth_bootstrap_url(
        SUPPORTED_RELEASES["2023.2"]
    )

    assert "account.amd.com" in bootstrap_url
    assert "xef.html" in bootstrap_url


def test_playwright_download_bootstraps_login_before_authenticated_http(mocker, tmp_path):
    strategy = object.__new__(PlaywrightDownloadStrategy)
    strategy.logger = type(
        "Logger",
        (),
        {
            "info": lambda *args, **kwargs: None,
            "warning": lambda *args, **kwargs: None,
        },
    )()
    strategy._launch_options = lambda: {"headless": True, "args": []}
    goto = mocker.patch.object(strategy, "_goto_with_retry")
    login = mocker.patch.object(strategy, "_login_if_needed")
    mocker.patch.object(strategy, "_fill_download_form_if_needed", return_value=None)
    session = requests.Session()
    mocker.patch.object(strategy, "_session_from_browser_context", return_value=session)

    destination = tmp_path / "installer.bin"
    release = SUPPORTED_RELEASES["2023.2"]
    credentials = VivadoCredentials(username="user", password="pass")

    fake_page = mocker.MagicMock()
    # Mock locator().count() and is_visible() for link checking
    fake_page.locator.return_value.first.count.return_value = 0
    fake_page.locator.return_value.first.is_visible.return_value = False

    # Mock context manager for expect_download
    fake_download = mocker.Mock()
    fake_download.suggested_filename = release.filename
    fake_download_info = mocker.Mock()
    fake_download_info.value = fake_download
    fake_page.expect_download.return_value.__enter__.return_value = fake_download_info

    # Mock page.on to trigger download event immediately
    def mock_on(event, callback):
        if event == "download":
            callback(fake_download)

    fake_page.on.side_effect = mock_on

    fake_context = mocker.Mock()
    fake_context.new_page.return_value = fake_page
    fake_browser = mocker.Mock()
    fake_browser.new_context.return_value = fake_context
    fake_chromium = mocker.Mock()
    fake_chromium.launch.return_value = fake_browser
    fake_playwright = mocker.Mock()
    fake_playwright.chromium = fake_chromium
    strategy._sync_playwright = mocker.MagicMock()
    strategy._sync_playwright.return_value.__enter__.return_value = fake_playwright
    strategy._sync_playwright.return_value.__exit__.return_value = None

    # We skip direct_download in this test because it returns the file from save_as
    # but we need to mock the download behavior

    result = strategy.download(release, destination, credentials)

    # It renames to suggested filename if different
    expected_target = destination.parent / release.filename
    assert result == expected_target
    goto.assert_called_once()
    call_args = goto.call_args[0]
    assert call_args[1] == strategy._auth_bootstrap_url(release)
    assert call_args[2] == "browser-login-navigation"
    assert goto.call_args[1]["credentials"] == credentials

    login.assert_called_once_with(fake_page, credentials)
    fake_download.save_as.assert_called_once_with(str(expected_target))
