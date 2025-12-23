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

"""Shared fixtures for download client tests."""

import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, Mock

import httpx
import pytest

from bookcard.pvr.base import DownloadClientSettings
from bookcard.pvr.download_clients.blackhole import (
    TorrentBlackholeSettings,
    UsenetBlackholeSettings,
)
from bookcard.pvr.download_clients.deluge import DelugeSettings
from bookcard.pvr.download_clients.download_station import DownloadStationSettings
from bookcard.pvr.download_clients.freebox_download import FreeboxDownloadSettings
from bookcard.pvr.download_clients.hadouken import HadoukenSettings
from bookcard.pvr.download_clients.nzbget import NzbgetSettings
from bookcard.pvr.download_clients.nzbvortex import NzbvortexSettings
from bookcard.pvr.download_clients.pneumatic import PneumaticSettings
from bookcard.pvr.download_clients.qbittorrent import QBittorrentSettings
from bookcard.pvr.download_clients.rtorrent import RTorrentSettings
from bookcard.pvr.download_clients.sabnzbd import SabnzbdSettings
from bookcard.pvr.download_clients.transmission import TransmissionSettings
from bookcard.pvr.download_clients.utorrent import UTorrentSettings
from bookcard.pvr.download_clients.vuze import VuzeSettings


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # Cleanup
    import shutil

    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def mock_httpx_response() -> MagicMock:
    """Create a mock httpx.Response."""
    response = MagicMock(spec=httpx.Response)
    response.status_code = 200
    response.text = "OK"
    response.content = b"OK"
    response.json.return_value = {"result": "success"}
    response.cookies = {}
    response.headers = {}
    response.raise_for_status = Mock()
    return response


@pytest.fixture
def mock_httpx_client(mock_httpx_response: MagicMock) -> MagicMock:
    """Create a mock httpx.Client."""
    client = MagicMock(spec=httpx.Client)
    client.get.return_value = mock_httpx_response
    client.post.return_value = mock_httpx_response
    client.delete.return_value = mock_httpx_response
    client.__enter__ = Mock(return_value=client)
    client.__exit__ = Mock(return_value=False)
    return client


@pytest.fixture
def base_download_client_settings() -> DownloadClientSettings:
    """Create base download client settings."""
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
def qbittorrent_settings(
    base_download_client_settings: DownloadClientSettings,
) -> QBittorrentSettings:
    """Create qBittorrent settings."""
    return QBittorrentSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        url_base=None,
    )


@pytest.fixture
def transmission_settings(
    base_download_client_settings: DownloadClientSettings,
) -> TransmissionSettings:
    """Create Transmission settings."""
    return TransmissionSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        url_base="/transmission/",
    )


@pytest.fixture
def sabnzbd_settings(
    base_download_client_settings: DownloadClientSettings,
) -> SabnzbdSettings:
    """Create SABnzbd settings."""
    return SabnzbdSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        url_base=None,
        api_key="test-api-key",
    )


@pytest.fixture
def torrent_blackhole_settings(temp_dir: Path) -> TorrentBlackholeSettings:
    """Create TorrentBlackhole settings."""
    return TorrentBlackholeSettings(
        host="localhost",
        port=8080,
        username=None,
        password=None,
        use_ssl=False,
        timeout_seconds=30,
        category=None,
        download_path=None,
        watch_folder=str(temp_dir / "watch"),
        torrent_folder=str(temp_dir / "torrents"),
        save_magnet_files=True,
        magnet_file_extension=".magnet",
    )


@pytest.fixture
def usenet_blackhole_settings(temp_dir: Path) -> UsenetBlackholeSettings:
    """Create UsenetBlackhole settings."""
    return UsenetBlackholeSettings(
        host="localhost",
        port=8080,
        username=None,
        password=None,
        use_ssl=False,
        timeout_seconds=30,
        category=None,
        download_path=None,
        watch_folder=str(temp_dir / "watch"),
        nzb_folder=str(temp_dir / "nzb"),
    )


@pytest.fixture
def deluge_settings(
    base_download_client_settings: DownloadClientSettings,
) -> DelugeSettings:
    """Create Deluge settings."""
    return DelugeSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def rtorrent_settings(
    base_download_client_settings: DownloadClientSettings,
) -> RTorrentSettings:
    """Create RTorrent settings."""
    return RTorrentSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        url_base="/RPC2",
    )


@pytest.fixture
def nzbget_settings(
    base_download_client_settings: DownloadClientSettings,
) -> NzbgetSettings:
    """Create NZBGet settings."""
    return NzbgetSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def download_station_settings(
    base_download_client_settings: DownloadClientSettings,
) -> DownloadStationSettings:
    """Create DownloadStation settings."""
    return DownloadStationSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        url_base="/webapi",
    )


@pytest.fixture
def freebox_download_settings(
    base_download_client_settings: DownloadClientSettings,
) -> FreeboxDownloadSettings:
    """Create FreeboxDownload settings."""
    return FreeboxDownloadSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
        app_id="test_app",
        app_token="test_token",
    )


@pytest.fixture
def hadouken_settings(
    base_download_client_settings: DownloadClientSettings,
) -> HadoukenSettings:
    """Create Hadouken settings."""
    return HadoukenSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def nzbvortex_settings(
    base_download_client_settings: DownloadClientSettings,
) -> NzbvortexSettings:
    """Create NZBVortex settings."""
    return NzbvortexSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def pneumatic_settings(
    base_download_client_settings: DownloadClientSettings,
) -> PneumaticSettings:
    """Create Pneumatic settings."""
    return PneumaticSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def utorrent_settings(
    base_download_client_settings: DownloadClientSettings,
) -> UTorrentSettings:
    """Create uTorrent settings."""
    return UTorrentSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def vuze_settings(
    base_download_client_settings: DownloadClientSettings,
) -> VuzeSettings:
    """Create Vuze settings."""
    return VuzeSettings(
        host=base_download_client_settings.host,
        port=base_download_client_settings.port,
        username=base_download_client_settings.username,
        password=base_download_client_settings.password,
        use_ssl=base_download_client_settings.use_ssl,
        timeout_seconds=base_download_client_settings.timeout_seconds,
        category=base_download_client_settings.category,
        download_path=base_download_client_settings.download_path,
    )


@pytest.fixture
def sample_torrent_file(temp_dir: Path) -> Path:
    """Create a sample torrent file for testing."""
    torrent_path = temp_dir / "test.torrent"
    torrent_path.write_bytes(
        b"d8:announce32:http://tracker.example.com/announce10:created by13:qBittorrent13:creation datei1234567890e4:infod6:lengthi1000e4:name9:test.torrent12:piece lengthi16384e6:pieces20:abcdefghijklmnopqrstee"
    )
    return torrent_path


@pytest.fixture
def sample_nzb_file(temp_dir: Path) -> Path:
    """Create a sample NZB file for testing."""
    nzb_path = temp_dir / "test.nzb"
    nzb_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nzb PUBLIC "-//newzBin//DTD NZB 1.0//EN" "http://www.newzbin.com/DTD/nzb/nzb-1.0.dtd">
<nzb xmlns="http://www.newzbin.com/DTD/2003/nzb">
  <file poster="test@example.com" date="1234567890" subject="test.nzb">
    <groups>
      <group>alt.binaries.test</group>
    </groups>
    <segments>
      <segment bytes="1000" number="1">test@example.com</segment>
    </segments>
  </file>
</nzb>"""
    nzb_path.write_bytes(nzb_content)
    return nzb_path


@pytest.fixture
def sample_magnet_link() -> str:
    """Create a sample magnet link for testing."""
    return "magnet:?xt=urn:btih:ABCDEF1234567890ABCDEF1234567890ABCDEF12&dn=test+book&tr=http://tracker.example.com"


@pytest.fixture
def sample_torrent_url() -> str:
    """Create a sample torrent URL for testing."""
    return "http://example.com/torrent.torrent"


@pytest.fixture
def sample_nzb_url() -> str:
    """Create a sample NZB URL for testing."""
    return "http://example.com/file.nzb"
