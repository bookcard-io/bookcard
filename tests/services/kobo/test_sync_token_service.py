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

"""Tests for SyncToken to achieve 100% coverage."""

from __future__ import annotations

import base64
import json
from datetime import UTC, datetime

import httpx
import pytest

from bookcard.services.kobo.sync_token_service import SyncToken, _parse_timestamp

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sync_token() -> SyncToken:
    """Create a default sync token.

    Returns
    -------
    SyncToken
        Sync token instance.
    """
    return SyncToken()


@pytest.fixture
def sync_token_with_timestamps() -> SyncToken:
    """Create a sync token with timestamps.

    Returns
    -------
    SyncToken
        Sync token instance with timestamps.
    """
    now = datetime.now(UTC)
    return SyncToken(
        books_last_modified=now,
        books_last_created=now,
        reading_state_last_modified=now,
        tags_last_modified=now,
        archive_last_modified=now,
    )


# ============================================================================
# Tests for _parse_timestamp
# ============================================================================


@pytest.mark.parametrize(
    ("ts_str", "expected_none"),
    [
        (None, True),
        ("", True),
        ("2025-01-15T12:00:00Z", False),
        ("2025-01-15T12:00:00+00:00", False),
        ("invalid", True),
    ],
)
def test_parse_timestamp(ts_str: str | None, expected_none: bool) -> None:
    """Test parsing timestamp string.

    Parameters
    ----------
    ts_str : str | None
        Timestamp string to parse.
    expected_none : bool
        Whether result should be None.
    """
    result = _parse_timestamp(ts_str)
    if expected_none:
        assert result is None
    else:
        assert result is not None
        assert result.tzinfo == UTC


# ============================================================================
# Tests for SyncToken.__init__
# ============================================================================


def test_sync_token_init_default() -> None:
    """Test SyncToken initialization with default values."""
    token = SyncToken()
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)
    assert token.books_last_created == datetime.min.replace(tzinfo=UTC)
    assert token.reading_state_last_modified == datetime.min.replace(tzinfo=UTC)
    assert token.tags_last_modified == datetime.min.replace(tzinfo=UTC)
    assert token.archive_last_modified == datetime.min.replace(tzinfo=UTC)


def test_sync_token_init_with_values() -> None:
    """Test SyncToken initialization with custom values."""
    now = datetime.now(UTC)
    token = SyncToken(
        books_last_modified=now,
        books_last_created=now,
    )
    assert token.books_last_modified == now
    assert token.books_last_created == now


# ============================================================================
# Tests for SyncToken.from_headers
# ============================================================================


def test_from_headers_no_header() -> None:
    """Test parsing sync token when header is missing."""
    headers: dict[str, str] = {}
    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_from_headers_empty_header() -> None:
    """Test parsing sync token when header is empty."""
    headers = {"x-kobo-sync": ""}
    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_from_headers_valid() -> None:
    """Test parsing sync token from valid header."""
    now = datetime.now(UTC)
    data = {
        "BooksLastModified": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "BooksLastCreated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    headers = {"x-kobo-sync": encoded}

    token = SyncToken.from_headers(headers)
    assert token.books_last_modified.date() == now.date()


def test_from_headers_invalid_base64() -> None:
    """Test parsing sync token when base64 is invalid."""
    headers = {"x-kobo-sync": "invalid_base64!!!"}
    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_from_headers_invalid_json() -> None:
    """Test parsing sync token when JSON is invalid."""
    invalid_json = base64.b64encode(b"invalid json").decode("utf-8")
    headers = {"x-kobo-sync": invalid_json}
    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_from_headers_missing_timestamps() -> None:
    """Test parsing sync token when timestamps are missing."""
    data = {}
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    headers = {"x-kobo-sync": encoded}

    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_from_headers_invalid_timestamp() -> None:
    """Test parsing sync token when timestamp is invalid."""
    data = {"BooksLastModified": "invalid-timestamp"}
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    headers = {"x-kobo-sync": encoded}

    token = SyncToken.from_headers(headers)
    assert token.books_last_modified == datetime.min.replace(tzinfo=UTC)


# ============================================================================
# Tests for SyncToken.to_headers
# ============================================================================


def test_to_headers_empty(sync_token: SyncToken) -> None:
    """Test adding sync token to headers when all timestamps are min.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    headers: dict[str, str] = {}
    sync_token.to_headers(headers)
    assert "x-kobo-sync" not in headers


def test_to_headers_with_timestamps(sync_token_with_timestamps: SyncToken) -> None:
    """Test adding sync token to headers with timestamps.

    Parameters
    ----------
    sync_token_with_timestamps : SyncToken
        Sync token instance with timestamps.
    """
    headers: dict[str, str] = {}
    sync_token_with_timestamps.to_headers(headers)
    assert "x-kobo-sync" in headers

    # Verify it can be decoded
    decoded = base64.b64decode(headers["x-kobo-sync"])
    data = json.loads(decoded.decode("utf-8"))
    assert "BooksLastModified" in data


def test_to_headers_partial_timestamps() -> None:
    """Test adding sync token to headers with partial timestamps."""
    now = datetime.now(UTC)
    token = SyncToken(books_last_modified=now)
    headers: dict[str, str] = {}
    token.to_headers(headers)
    assert "x-kobo-sync" in headers


# ============================================================================
# Tests for SyncToken.merge_from_store_response
# ============================================================================


def test_merge_from_store_response_no_header(sync_token: SyncToken) -> None:
    """Test merging when response has no sync header.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    response = httpx.Response(200, headers={})
    original_modified = sync_token.books_last_modified
    sync_token.merge_from_store_response(response)
    assert sync_token.books_last_modified == original_modified


def test_merge_from_store_response_valid(sync_token: SyncToken) -> None:
    """Test merging when response has valid sync header.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    now = datetime.now(UTC)
    future = datetime(now.year + 1, 1, 1, tzinfo=UTC)
    data = {
        "BooksLastModified": future.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    response = httpx.Response(200, headers={"x-kobo-sync": encoded})

    sync_token.merge_from_store_response(response)
    assert sync_token.books_last_modified.date() == future.date()


def test_merge_from_store_response_invalid(sync_token: SyncToken) -> None:
    """Test merging when response has invalid sync header.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    response = httpx.Response(200, headers={"x-kobo-sync": "invalid!!!"})
    original_modified = sync_token.books_last_modified
    sync_token.merge_from_store_response(response)
    assert sync_token.books_last_modified == original_modified


def test_merge_from_store_response_older_timestamp(
    sync_token_with_timestamps: SyncToken,
) -> None:
    """Test merging when store timestamp is older.

    Parameters
    ----------
    sync_token_with_timestamps : SyncToken
        Sync token instance with timestamps.
    """
    past = datetime(2000, 1, 1, tzinfo=UTC)
    data = {
        "BooksLastModified": past.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    json_str = json.dumps(data)
    encoded = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    response = httpx.Response(200, headers={"x-kobo-sync": encoded})

    original_modified = sync_token_with_timestamps.books_last_modified
    sync_token_with_timestamps.merge_from_store_response(response)
    assert sync_token_with_timestamps.books_last_modified == original_modified


# ============================================================================
# Tests for SyncToken._merge_timestamp
# ============================================================================


def test_merge_timestamp_key_missing(sync_token: SyncToken) -> None:
    """Test merging timestamp when key is missing.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    data: dict[str, object] = {}
    original = sync_token.books_last_modified
    sync_token._merge_timestamp(data, "BooksLastModified", "books_last_modified")
    assert sync_token.books_last_modified == original


def test_merge_timestamp_invalid_string(sync_token: SyncToken) -> None:
    """Test merging timestamp when value is invalid string.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    data = {"BooksLastModified": "invalid"}
    original = sync_token.books_last_modified
    sync_token._merge_timestamp(data, "BooksLastModified", "books_last_modified")
    assert sync_token.books_last_modified == original


def test_merge_timestamp_non_string(sync_token: SyncToken) -> None:
    """Test merging timestamp when value is not a string.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    data = {"BooksLastModified": 12345}
    sync_token._merge_timestamp(data, "BooksLastModified", "books_last_modified")
    # Should not change since 12345 is not a valid timestamp string
    assert sync_token.books_last_modified == datetime.min.replace(tzinfo=UTC)


def test_merge_timestamp_none_value(sync_token: SyncToken) -> None:
    """Test merging timestamp when value is None.

    Parameters
    ----------
    sync_token : SyncToken
        Sync token instance.
    """
    data = {"BooksLastModified": None}
    original = sync_token.books_last_modified
    sync_token._merge_timestamp(data, "BooksLastModified", "books_last_modified")
    assert sync_token.books_last_modified == original
