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

"""Type definitions for matching results."""

from dataclasses import dataclass

from fundamental.services.library_scanning.data_sources.types import AuthorData


@dataclass
class MatchResult:
    """Result of matching an entity to an external data source.

    Attributes
    ----------
    confidence_score : float
        Confidence score between 0.0 and 1.0.
    matched_entity : AuthorData
        Matched author data from external source.
    match_method : str
        Method used for matching (e.g., "identifier", "exact", "fuzzy").
    calibre_author_id : int | None
        ID of the Calibre author that was matched (for tracking).
    """

    confidence_score: float
    matched_entity: AuthorData
    match_method: str
    calibre_author_id: int | None = None
