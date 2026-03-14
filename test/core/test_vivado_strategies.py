"""Tests for the modular Vivado download strategies."""

from pathlib import Path

from adibuild.core.vivado import (
    SUPPORTED_RELEASES,
    VivadoCredentials,
    VivadoInstaller,
)


def test_strategy_selection_order(mocker):
    """Verify that strategies are tried in the correct order."""
    from adibuild.core.vivado import VivadoDownloadError

    # Mock all strategies
    mock_docker = mocker.patch("adibuild.core.vivado.DockerDownloadStrategy")
    mock_session = mocker.patch("adibuild.core.vivado.SessionDownloadStrategy")
    mock_playwright = mocker.patch("adibuild.core.vivado.PlaywrightDownloadStrategy")
    mock_selenium = mocker.patch("adibuild.core.vivado.SeleniumDownloadStrategy")
    mock_requests = mocker.patch("adibuild.core.vivado.RequestsDownloadStrategy")

    # Force failure on early strategies to see the fallback
    mock_docker.return_value.download.side_effect = VivadoDownloadError("Docker failed")
    mock_session.return_value.download.side_effect = VivadoDownloadError("Session failed")
    mock_playwright.return_value.download.side_effect = VivadoDownloadError(
        "Playwright failed"
    )
    mock_selenium.return_value.download.side_effect = VivadoDownloadError(
        "Selenium failed"
    )

    installer = VivadoInstaller()
    SUPPORTED_RELEASES["2023.2"]
    credentials = VivadoCredentials(username="u", password="p")

    # We expect it to try all and eventually fail or call requests
    try:
        installer.download_installer("2023.2", credentials=credentials)
    except Exception:
        pass

    # Verify calls
    assert mock_docker.return_value.download.called
    assert mock_session.return_value.download.called
    assert mock_playwright.return_value.download.called
    assert mock_selenium.return_value.download.called
    assert mock_requests.return_value.download.called


def test_download_installer_retries_on_failure(mocker):
    """Verify that download_installer retries after a failure."""
    from adibuild.core.vivado import VivadoDownloadError

    # Mock all strategies
    mock_docker = mocker.patch("adibuild.core.vivado.DockerDownloadStrategy")
    mock_session = mocker.patch("adibuild.core.vivado.SessionDownloadStrategy")
    mock_playwright = mocker.patch("adibuild.core.vivado.PlaywrightDownloadStrategy")
    mock_selenium = mocker.patch("adibuild.core.vivado.SeleniumDownloadStrategy")
    mock_requests = mocker.patch("adibuild.core.vivado.RequestsDownloadStrategy")

    # All fail on first call
    success_path = mocker.MagicMock(spec=Path)
    mock_docker.return_value.download.side_effect = [
        VivadoDownloadError("F1"),
        success_path,
    ]
    mock_session.return_value.download.side_effect = VivadoDownloadError("F1")
    mock_playwright.return_value.download.side_effect = VivadoDownloadError("F1")
    mock_selenium.return_value.download.side_effect = VivadoDownloadError("F1")
    mock_requests.return_value.download.side_effect = VivadoDownloadError("F1")

    # Mock prefer_browser_download to always return True for this test
    mocker.patch(
        "adibuild.core.vivado.VivadoInstaller._prefer_browser_download", return_value=True
    )
    mocker.patch("adibuild.core.vivado.VivadoInstaller.verify_installer")
    mocker.patch("time.sleep")

    installer = VivadoInstaller()
    credentials = VivadoCredentials(username="u", password="p")

    result = installer.download_installer("2023.2", credentials=credentials)

    assert result == success_path
    assert mock_docker.return_value.download.call_count == 2
