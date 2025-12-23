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

"""Tests for torrent utility functions."""

import pytest

from bookcard.pvr.utils.torrent import extract_hash_from_magnet


class TestExtractHashFromMagnet:
    """Test extract_hash_from_magnet function."""

    def test_extract_hash_simple(self) -> None:
        """Test extract_hash_from_magnet with simple magnet link (no & separator)."""
        # Function splits by "&", so simple links without "&" won't match
        # because "magnet:?xt=urn:btih:ABC123" doesn't start with "xt=urn:btih:"
        magnet = "magnet:?xt=urn:btih:ABC123DEF456"
        result = extract_hash_from_magnet(magnet)
        assert result is None

    def test_extract_hash_with_additional_params(self) -> None:
        """Test extract_hash_from_magnet with additional parameters."""
        # After splitting by "&", we get parts that start with "xt=urn:btih:"
        magnet = "xt=urn:btih:abc123&dn=example&tr=http://tracker.com"
        result = extract_hash_from_magnet(magnet)
        assert result == "ABC123"

    def test_extract_hash_lowercase(self) -> None:
        """Test extract_hash_from_magnet converts to uppercase."""
        magnet = "xt=urn:btih:abc123def456&dn=test"
        result = extract_hash_from_magnet(magnet)
        assert result == "ABC123DEF456"

    def test_extract_hash_mixed_case(self) -> None:
        """Test extract_hash_from_magnet with mixed case hash."""
        magnet = "xt=urn:btih:AbC123DeF456&dn=test"
        result = extract_hash_from_magnet(magnet)
        assert result == "ABC123DEF456"

    @pytest.mark.parametrize(
        ("magnet", "expected"),
        [
            ("xt=urn:btih:ABC123&dn=test", "ABC123"),
            ("xt=urn:btih:1234567890abcdef&dn=test", "1234567890ABCDEF"),
            ("xt=urn:btih:ABCDEF123456&tr=tracker1&tr=tracker2", "ABCDEF123456"),
            ("xt=urn:btih:abc&dn=Test%20Name", "ABC"),
        ],
    )
    def test_extract_hash_various_formats(self, magnet: str, expected: str) -> None:
        """Test extract_hash_from_magnet with various magnet link formats."""
        result = extract_hash_from_magnet(magnet)
        assert result == expected

    def test_extract_hash_not_found(self) -> None:
        """Test extract_hash_from_magnet returns None when hash not found."""
        magnet = "magnet:?dn=example&tr=http://tracker.com"
        result = extract_hash_from_magnet(magnet)
        assert result is None

    def test_extract_hash_no_xt_param(self) -> None:
        """Test extract_hash_from_magnet returns None when no xt parameter."""
        magnet = "magnet:?dn=example"
        result = extract_hash_from_magnet(magnet)
        assert result is None

    def test_extract_hash_wrong_urn(self) -> None:
        """Test extract_hash_from_magnet returns None when wrong URN."""
        magnet = "magnet:?xt=urn:sha1:ABC123"
        result = extract_hash_from_magnet(magnet)
        assert result is None

    def test_extract_hash_empty_string(self) -> None:
        """Test extract_hash_from_magnet with empty string."""
        result = extract_hash_from_magnet("")
        assert result is None

    def test_extract_hash_no_colon_after_btih(self) -> None:
        """Test extract_hash_from_magnet handles edge case with no colon."""
        # "xt=urn:btihABC123" doesn't start with "xt=urn:btih:" so won't match
        magnet = "xt=urn:btihABC123&dn=test"
        result = extract_hash_from_magnet(magnet)
        assert result is None

    def test_extract_hash_multiple_xt_params(self) -> None:
        """Test extract_hash_from_magnet uses first xt=urn:btih: parameter found after split."""
        # After splitting by "&", first part is "magnet:?xt=urn:btih:FIRST" (doesn't start with "xt=urn:btih:")
        # Second part is "xt=urn:btih:SECOND" (does start with "xt=urn:btih:")
        magnet = "magnet:?xt=urn:btih:FIRST&xt=urn:btih:SECOND"
        result = extract_hash_from_magnet(magnet)
        # Function finds first part after splitting that starts with "xt=urn:btih:"
        assert result == "SECOND"
