# Copyright (C) 2025 knguyen and others
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Shared fixtures for Direct HTTP download client tests."""

from __future__ import annotations

import tempfile
from pathlib import Path
from threading import Event
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import httpx
import pytest
from bs4 import BeautifulSoup

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.direct_http.settings import DirectHttpSettings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing.

    Yields
    ------
    Path
        Temporary directory path.
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    import shutil

    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def direct_http_settings() -> DirectHttpSettings:
    """Create DirectHttpSettings for testing.

    Returns
    -------
    DirectHttpSettings
        Settings instance.
    """
    return DirectHttpSettings(
        host="localhost",
        port=8080,
        username="testuser",
        password="testpass",
        use_ssl=False,
        timeout_seconds=30,
        category="test",
        download_path="/downloads",
        aa_donator_key=None,
        flaresolverr_url="http://flaresolverr:8191",
        flaresolverr_path="/v1",
        flaresolverr_timeout=60000,
        use_seleniumbase=False,
    )


@pytest.fixture
def base_download_client_settings() -> DownloadClientSettings:
    """Create base DownloadClientSettings for testing.

    Returns
    -------
    DownloadClientSettings
        Settings instance.
    """
    return DownloadClientSettings(
        host="localhost",
        port=8080,
        username="testuser",
        password="testpass",
        use_ssl=False,
        timeout_seconds=30,
        category="test",
        download_path="/downloads",
    )


@pytest.fixture
def mock_streaming_response() -> MagicMock:
    """Create a mock streaming HTTP response.

    Returns
    -------
    MagicMock
        Mock response with streaming capabilities.
    """
    response = MagicMock()
    response.status_code = 200
    response.text = "<html><body>Test</body></html>"
    response.headers = httpx.Headers({
        "content-type": "text/html",
        "content-length": "1000",
    })
    response.raise_for_status = Mock()
    response.iter_bytes = Mock(return_value=iter([b"chunk1", b"chunk2", b"chunk3"]))
    return response


@pytest.fixture
def mock_streaming_client(mock_streaming_response: MagicMock) -> MagicMock:
    """Create a mock streaming HTTP client.

    Parameters
    ----------
    mock_streaming_response : MagicMock
        Mock response to return.

    Returns
    -------
    MagicMock
        Mock client with streaming capabilities.
    """
    client = MagicMock()
    client.get.return_value = mock_streaming_response
    client.stream.return_value.__enter__ = Mock(return_value=mock_streaming_response)
    client.stream.return_value.__exit__ = Mock(return_value=False)
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    return client


@pytest.fixture
def mock_http_client_factory(
    mock_streaming_client: MagicMock,
) -> Callable[[], MagicMock]:
    """Create a factory function for mock HTTP clients.

    Parameters
    ----------
    mock_streaming_client : MagicMock
        Mock client to return.

    Returns
    -------
    Callable[[], MagicMock]
        Factory function.
    """
    return lambda: mock_streaming_client


@pytest.fixture
def mock_file_fetcher() -> MagicMock:
    """Create a mock file fetcher.

    Returns
    -------
    MagicMock
        Mock file fetcher.
    """
    fetcher = MagicMock()
    fetcher.fetch_file = Mock(return_value=b"file content")
    return fetcher


@pytest.fixture
def mock_url_router() -> MagicMock:
    """Create a mock URL router.

    Returns
    -------
    MagicMock
        Mock URL router.
    """
    router = MagicMock()
    router.route = Mock(return_value="https://example.com/file.pdf")
    return router


@pytest.fixture
def sample_anna_archive_url() -> str:
    """Create a sample Anna's Archive URL.

    Returns
    -------
    str
        Sample URL.
    """
    return "https://annas-archive.li/md5/1234567890abcdef1234567890abcdef"


@pytest.fixture
def sample_direct_url() -> str:
    """Create a sample direct download URL.

    Returns
    -------
    str
        Sample URL.
    """
    return "https://example.com/file.pdf"


@pytest.fixture
def sample_html() -> str:
    """Create sample HTML content.

    Returns
    -------
    str
        HTML string.
    """
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <a href="https://example.com/download.pdf">Download</a>
            <span class="js-partner-countdown">5</span>
        </body>
    </html>
    """


@pytest.fixture
def sample_soup(sample_html: str) -> BeautifulSoup:
    """Create a BeautifulSoup instance from sample HTML.

    Parameters
    ----------
    sample_html : str
        HTML content.

    Returns
    -------
    BeautifulSoup
        Parsed soup.
    """
    return BeautifulSoup(sample_html, "html.parser")


@pytest.fixture
def mock_time_provider() -> MagicMock:
    """Create a mock time provider.

    Returns
    -------
    MagicMock
        Mock time provider.
    """
    provider = MagicMock()
    provider.time = Mock(return_value=1000.0)
    provider.sleep = Mock()
    return provider


@pytest.fixture
def mock_driver() -> MagicMock:
    """Create a mock SeleniumBase driver.

    Returns
    -------
    MagicMock
        Mock driver.
    """
    driver = MagicMock()
    driver.get_current_url = Mock(return_value="https://example.com")
    driver.get_title = Mock(return_value="Test Page")
    driver.get_text = Mock(return_value="Test content")
    driver.page_source = "<html><body>Test</body></html>"
    driver.get_cookies = Mock(return_value=[])
    driver.execute_script = Mock(return_value="result")
    driver.reconnect = Mock()
    driver.activate_cdp_mode = Mock()
    driver.uc_gui_handle_captcha = Mock()
    driver.uc_gui_click_captcha = Mock()
    driver.refresh = Mock()
    driver.close = Mock()
    driver.quit = Mock()
    driver.add_cookie = Mock()
    driver.uc_open_with_reconnect = Mock()
    driver.cdp = MagicMock()
    driver.cdp.solve_captcha = Mock()
    driver.cdp.click = Mock()
    driver.cdp.gui_click_captcha = Mock()
    driver.cdp.gui_click_element = Mock()
    driver.cdp.is_element_visible = Mock(return_value=True)
    driver.cdp.driver = MagicMock()
    driver.cdp.driver.stop = Mock()
    return driver


@pytest.fixture
def cancel_flag() -> Event:
    """Create a cancellation flag.

    Returns
    -------
    Event
        Threading event for cancellation.
    """
    return Event()


@pytest.fixture
def mock_bypass_result() -> MagicMock:
    """Create a mock bypass result.

    Returns
    -------
    MagicMock
        Mock result.
    """
    result = MagicMock()
    result.success = True
    result.html = "<html><body>Bypassed</body></html>"
    result.error = None
    return result


@pytest.fixture
def mock_bypass_strategy(mock_bypass_result: MagicMock) -> MagicMock:
    """Create a mock bypass strategy.

    Parameters
    ----------
    mock_bypass_result : MagicMock
        Result to return.

    Returns
    -------
    MagicMock
        Mock strategy.
    """
    strategy = MagicMock()
    strategy.fetch = Mock(return_value=mock_bypass_result)
    strategy.validate_dependencies = Mock()
    return strategy


@pytest.fixture
def mock_process_manager() -> MagicMock:
    """Create a mock process manager.

    Returns
    -------
    MagicMock
        Mock process manager.
    """
    manager = MagicMock()
    manager.cleanup_orphans = Mock(return_value=0)
    manager.force_kill_chrome = Mock()
    return manager


@pytest.fixture
def mock_display_manager() -> MagicMock:
    """Create a mock display manager.

    Returns
    -------
    MagicMock
        Mock display manager.
    """
    manager = MagicMock()
    manager.ensure_initialized = Mock()
    manager.cleanup = Mock()
    return manager


@pytest.fixture
def mock_driver_factory(mock_driver: MagicMock) -> MagicMock:
    """Create a mock driver factory.

    Parameters
    ----------
    mock_driver : MagicMock
        Driver to return.

    Returns
    -------
    MagicMock
        Mock factory.
    """
    factory = MagicMock()
    factory.create = Mock(return_value=mock_driver)
    factory.get_screen_size = Mock(return_value=(1920, 1080))
    return factory


@pytest.fixture
def mock_driver_manager() -> MagicMock:
    """Create a mock driver manager.

    Returns
    -------
    MagicMock
        Mock driver manager.
    """
    manager = MagicMock()
    manager.quit = Mock()
    return manager


@pytest.fixture
def mock_cookie_store() -> MagicMock:
    """Create a mock cookie store.

    Returns
    -------
    MagicMock
        Mock cookie store.
    """
    store = MagicMock()
    store.get = Mock(return_value={})
    store.set = Mock()
    store.get_cookie_values_for_url = Mock(return_value={})
    store.get_cookie_dicts_for_url = Mock(return_value=[])
    store.extract_from_driver = Mock()
    return store


@pytest.fixture
def mock_user_agent_store() -> MagicMock:
    """Create a mock user agent store.

    Returns
    -------
    MagicMock
        Mock user agent store.
    """
    store = MagicMock()
    store.get = Mock(return_value=None)
    store.set = Mock()
    store.get_user_agent_for_url = Mock(return_value=None)
    store.extract_from_driver = Mock()
    return store


@pytest.fixture
def mock_challenge_detector() -> MagicMock:
    """Create a mock challenge detector.

    Returns
    -------
    MagicMock
        Mock detector.
    """
    detector = MagicMock()
    detector.detect = Mock(return_value="none")
    detector.get_name = Mock(return_value="none")
    return detector


@pytest.fixture
def mock_success_checker() -> MagicMock:
    """Create a mock success checker.

    Returns
    -------
    MagicMock
        Mock checker.
    """
    checker = MagicMock()
    checker.is_bypassed = Mock(return_value=True)
    return checker


@pytest.fixture
def mock_bypass_method() -> MagicMock:
    """Create a mock bypass method.

    Returns
    -------
    MagicMock
        Mock method.
    """
    method = MagicMock()
    method.attempt = Mock(return_value=True)
    method.get_name = Mock(return_value="test_method")
    return method


@pytest.fixture
def mock_state_manager() -> MagicMock:
    """Create a mock download state manager.

    Returns
    -------
    MagicMock
        Mock state manager.
    """
    manager = MagicMock()
    manager.create = Mock()
    manager.update_status = Mock()
    manager.update_info = Mock()
    manager.update_progress = Mock()
    manager.get_all = Mock(return_value=[])
    manager.remove = Mock(return_value=True)
    manager.cleanup_old = Mock()
    return manager


@pytest.fixture
def mock_filename_resolver() -> MagicMock:
    """Create a mock filename resolver.

    Returns
    -------
    MagicMock
        Mock resolver.
    """
    resolver = MagicMock()
    resolver.resolve = Mock(return_value="test_file.pdf")
    return resolver


@pytest.fixture
def mock_html_parser(sample_soup: BeautifulSoup) -> MagicMock:
    """Create a mock HTML parser.

    Parameters
    ----------
    sample_soup : BeautifulSoup
        Soup to return.

    Returns
    -------
    MagicMock
        Mock parser.
    """
    parser = MagicMock()
    parser.parse = Mock(return_value=sample_soup)
    return parser


@pytest.fixture
def mock_url_resolver() -> MagicMock:
    """Create a mock URL resolver.

    Returns
    -------
    MagicMock
        Mock resolver.
    """
    resolver = MagicMock()
    resolver.can_resolve = Mock(return_value=True)
    resolver.resolve = Mock(return_value="https://example.com/resolved")
    return resolver


@pytest.fixture
def mock_file_downloader() -> MagicMock:
    """Create a mock file downloader.

    Returns
    -------
    MagicMock
        Mock downloader.
    """
    downloader = MagicMock()
    downloader.download = Mock()
    return downloader


@pytest.fixture(params=[True, False])
def use_seleniumbase(request: pytest.FixtureRequest) -> bool:
    """Parametrized fixture for use_seleniumbase setting.

    Parameters
    ----------
    request : pytest.FixtureRequest
        Pytest request object.

    Returns
    -------
    bool
        Value of use_seleniumbase.
    """
    return request.param


@pytest.fixture(
    params=[
        "https://annas-archive.li/md5/1234567890abcdef1234567890abcdef",
        "https://annas-archive.se/md5/abcdef1234567890abcdef1234567890",
        "https://example.com/file.pdf",
        "https://libgen.li/ads.php?md5=1234567890abcdef1234567890abcdef",
    ]
)
def sample_url(request: pytest.FixtureRequest) -> str:
    """Parametrized fixture for various URL types.

    Parameters
    ----------
    request : pytest.FixtureRequest
        Pytest request object.

    Returns
    -------
    str
        Sample URL.
    """
    return request.param


@pytest.fixture(
    params=[
        (200, "OK"),
        (403, "Forbidden"),
        (404, "Not Found"),
        (429, "Too Many Requests"),
        (503, "Service Unavailable"),
    ]
)
def http_status_code_and_message(request: pytest.FixtureRequest) -> tuple[int, str]:
    """Parametrized fixture for HTTP status codes.

    Parameters
    ----------
    request : pytest.FixtureRequest
        Pytest request object.

    Returns
    -------
    tuple[int, str]
        Status code and message.
    """
    return request.param
