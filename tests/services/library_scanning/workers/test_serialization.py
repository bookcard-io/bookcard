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

"""Tests for serialization helpers to achieve 100% coverage."""

from typing import Any

import pytest

from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    IdentifierDict,
)
from fundamental.services.library_scanning.matching.types import MatchResult
from fundamental.services.library_scanning.workers.serialization import (
    deserialize_match_result,
)


@pytest.fixture
def author_data_dict() -> dict[str, Any]:
    """Create author data dictionary.

    Returns
    -------
    dict[str, Any]
        Author data dict.
    """
    return {
        "key": "OL123A",
        "name": "Test Author",
        "personal_name": "Test",
        "fuller_name": "Test Author",
    }


@pytest.fixture
def author_data_dict_with_identifiers() -> dict[str, Any]:
    """Create author data dictionary with identifiers.

    Returns
    -------
    dict[str, Any]
        Author data dict with identifiers.
    """
    return {
        "key": "OL123A",
        "name": "Test Author",
        "identifiers": {
            "isni": "0000000123456789",
            "viaf": "123456789",
        },
    }


class TestDeserializeMatchResult:
    """Test deserialize_match_result function."""

    def test_deserialize_with_identifiers(
        self, author_data_dict_with_identifiers: dict[str, Any]
    ) -> None:
        """Test deserialize with identifiers (covers lines 40-50).

        Parameters
        ----------
        author_data_dict_with_identifiers : dict[str, Any]
            Author data with identifiers.
        """
        data = {
            "confidence_score": 0.9,
            "matched_entity": author_data_dict_with_identifiers,
            "match_method": "identifier",
            "calibre_author_id": 1,
        }
        result = deserialize_match_result(data)

        assert isinstance(result, MatchResult)
        assert result.confidence_score == 0.9
        assert result.match_method == "identifier"
        assert result.calibre_author_id == 1
        assert isinstance(result.matched_entity, AuthorData)
        assert result.matched_entity.key == "OL123A"
        assert isinstance(result.matched_entity.identifiers, IdentifierDict)
        assert result.matched_entity.identifiers.isni == "0000000123456789"
        assert result.matched_entity.identifiers.viaf == "123456789"

    def test_deserialize_without_identifiers(
        self, author_data_dict: dict[str, Any]
    ) -> None:
        """Test deserialize without identifiers.

        Parameters
        ----------
        author_data_dict : dict[str, Any]
            Author data without identifiers.
        """
        data = {
            "confidence_score": 0.8,
            "matched_entity": author_data_dict,
            "match_method": "fuzzy",
        }
        result = deserialize_match_result(data)

        assert isinstance(result, MatchResult)
        assert result.confidence_score == 0.8
        assert result.match_method == "fuzzy"
        assert result.calibre_author_id is None
        assert isinstance(result.matched_entity, AuthorData)
        assert result.matched_entity.key == "OL123A"
        assert result.matched_entity.identifiers is None

    def test_deserialize_with_none_identifiers(
        self, author_data_dict: dict[str, Any]
    ) -> None:
        """Test deserialize with None identifiers.

        Parameters
        ----------
        author_data_dict : dict[str, Any]
            Author data.
        """
        author_data_dict["identifiers"] = None
        data = {
            "confidence_score": 0.7,
            "matched_entity": author_data_dict,
            "match_method": "exact",
            "calibre_author_id": 2,
        }
        result = deserialize_match_result(data)

        assert isinstance(result, MatchResult)
        assert result.matched_entity.identifiers is None
