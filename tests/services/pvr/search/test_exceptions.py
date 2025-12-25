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

"""Tests for custom exceptions."""

import pytest

from bookcard.services.pvr.search.exceptions import (
    IndexerSearchError,
    IndexerTimeoutError,
    IndexerUnavailableError,
)


class TestIndexerSearchError:
    """Test IndexerSearchError exception."""

    def test_base_exception(self) -> None:
        """Test base exception can be raised and caught."""
        with pytest.raises(IndexerSearchError, match="test error"):
            raise IndexerSearchError("test error")

    def test_exception_message(self) -> None:
        """Test exception message is preserved."""
        error = IndexerSearchError("Custom error message")
        assert str(error) == "Custom error message"


class TestIndexerTimeoutError:
    """Test IndexerTimeoutError exception."""

    def test_inherits_from_base(self) -> None:
        """Test IndexerTimeoutError inherits from IndexerSearchError."""
        with pytest.raises(IndexerSearchError):
            raise IndexerTimeoutError("timeout")

        with pytest.raises(IndexerTimeoutError):
            raise IndexerTimeoutError("timeout")

    def test_exception_message(self) -> None:
        """Test exception message is preserved."""
        error = IndexerTimeoutError("Search timed out after 30s")
        assert str(error) == "Search timed out after 30s"


class TestIndexerUnavailableError:
    """Test IndexerUnavailableError exception."""

    def test_inherits_from_base(self) -> None:
        """Test IndexerUnavailableError inherits from IndexerSearchError."""
        with pytest.raises(IndexerSearchError):
            raise IndexerUnavailableError("unavailable")

        with pytest.raises(IndexerUnavailableError):
            raise IndexerUnavailableError("unavailable")

    def test_exception_message(self) -> None:
        """Test exception message is preserved."""
        error = IndexerUnavailableError("Indexer is currently unavailable")
        assert str(error) == "Indexer is currently unavailable"
