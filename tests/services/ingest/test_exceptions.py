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

"""Tests for ingest exceptions to achieve 100% coverage."""

from __future__ import annotations

import pytest

from fundamental.services.ingest.exceptions import (
    IngestError,
    IngestHistoryCreationError,
    IngestHistoryNotFoundError,
)


@pytest.mark.parametrize(
    ("history_id", "expected_message"),
    [
        (1, "Ingest history 1 not found"),
        (42, "Ingest history 42 not found"),
        (999, "Ingest history 999 not found"),
    ],
)
def test_ingest_history_not_found_error(history_id: int, expected_message: str) -> None:
    """Test IngestHistoryNotFoundError initialization and attributes."""
    error = IngestHistoryNotFoundError(history_id)
    assert str(error) == expected_message
    assert error.history_id == history_id
    assert isinstance(error, IngestError)


def test_ingest_history_creation_error() -> None:
    """Test IngestHistoryCreationError can be instantiated."""
    error = IngestHistoryCreationError()
    assert isinstance(error, IngestError)


def test_ingest_error() -> None:
    """Test IngestError base exception can be instantiated."""
    error = IngestError()
    assert isinstance(error, Exception)
