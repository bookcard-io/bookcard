# Copyright (C) 2026 knguyen and others
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

from unittest.mock import MagicMock, patch

import pytest

from bookcard.pvr.indexers.annas_archive import (
    AnnasArchiveIndexer,
    AnnasArchiveSettings,
)


@pytest.fixture
def annas_archive_settings() -> AnnasArchiveSettings:
    return AnnasArchiveSettings(
        base_url="https://annas-archive.org",
    )


@pytest.fixture
def annas_archive_indexer(
    annas_archive_settings: AnnasArchiveSettings,
) -> AnnasArchiveIndexer:
    return AnnasArchiveIndexer(settings=annas_archive_settings)


class TestAnnasArchiveIndexer:
    @patch("bookcard.pvr.indexers.annas_archive.network.httpx.Client")
    def test_search_priority_logic(
        self, mock_client: MagicMock, annas_archive_indexer: AnnasArchiveIndexer
    ) -> None:
        """Test that search terms are prioritized correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html></html>"
        mock_client_instance = MagicMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__enter__.return_value = mock_client_instance

        # Case 1: Title and Author provided -> should be used
        annas_archive_indexer.search(
            query="query", title="Title", author="Author", isbn="9780132350884"
        )
        call_args = mock_client_instance.get.call_args
        # Only check if params.q matches what we expect
        assert call_args[1]["params"]["q"] == "Title Author"

        # Case 2: Title provided -> should be used over Query and ISBN
        annas_archive_indexer.search(query="query", title="Title", isbn="9780132350884")
        call_args = mock_client_instance.get.call_args
        assert call_args[1]["params"]["q"] == "Title"

        # Case 3: Query provided, no Title -> should be used over ISBN
        annas_archive_indexer.search(query="query", isbn="9780132350884")
        call_args = mock_client_instance.get.call_args
        assert call_args[1]["params"]["q"] == "query"

        # Case 4: Only ISBN provided -> should be used
        annas_archive_indexer.search(query="", isbn="9780132350884")
        call_args = mock_client_instance.get.call_args
        assert call_args[1]["params"]["q"] == "9780132350884"
