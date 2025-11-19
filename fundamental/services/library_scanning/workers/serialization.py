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

"""Serialization helpers for workers."""

from typing import Any

from fundamental.services.library_scanning.data_sources.types import (
    AuthorData,
    IdentifierDict,
)
from fundamental.services.library_scanning.matching.types import MatchResult


def deserialize_match_result(data: dict[str, Any]) -> MatchResult:
    """Deserialize a dictionary to MatchResult object.

    Parameters
    ----------
    data : dict[str, Any]
        Dictionary representation of MatchResult.

    Returns
    -------
    MatchResult
        Reconstructed object.
    """
    entity_data = data["matched_entity"].copy()

    # Handle IdentifierDict nesting
    if entity_data.get("identifiers"):
        entity_data["identifiers"] = IdentifierDict(**entity_data["identifiers"])

    # Handle simple fields (ensure no extra fields cause error if strict)
    # AuthorData is a dataclass, so **kwargs works if keys match.
    entity = AuthorData(**entity_data)

    return MatchResult(
        confidence_score=data["confidence_score"],
        matched_entity=entity,
        match_method=data["match_method"],
        calibre_author_id=data.get("calibre_author_id"),
    )
