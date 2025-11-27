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

"""Metadata extraction utilities.

Follows DRY by centralizing metadata extraction logic.
"""

from dataclasses import dataclass, field

from fundamental.models.ingest import IngestHistory


@dataclass
class ExtractedMetadata:
    """Metadata extracted from various sources.

    Attributes
    ----------
    title : str | None
        Extracted title.
    authors : list[str]
        Extracted authors list.
    isbn : str | None
        Extracted ISBN.
    """

    title: str | None = None
    authors: list[str] = field(default_factory=list)
    isbn: str | None = None

    @property
    def primary_author(self) -> str | None:
        """Get primary author (first in list).

        Returns
        -------
        str | None
            Primary author name, or None if no authors.
        """
        return self.authors[0] if self.authors else None


def _build_metadata_sources(
    history: IngestHistory, metadata_hint: dict | None = None
) -> list[dict]:
    """Build list of metadata sources in priority order.

    Parameters
    ----------
    history : IngestHistory
        Ingest history record.
    metadata_hint : dict | None
        Optional explicit metadata hint.

    Returns
    -------
    list[dict]
        List of metadata sources in priority order.
    """
    sources: list[dict] = []

    # Priority 1: Explicit hint
    if metadata_hint:
        sources.append(metadata_hint)

    # Priority 2: History's metadata_hint
    if history.ingest_metadata:
        hint = history.ingest_metadata.get("metadata_hint", {})
        if hint:
            sources.append(hint)

    # Priority 3: History's fetched_metadata
    if history.ingest_metadata:
        fetched = history.ingest_metadata.get("fetched_metadata", {})
        if fetched:
            sources.append(fetched)

    return sources


def _extract_from_source(source: dict, result: ExtractedMetadata) -> None:
    """Extract metadata fields from a single source into result.

    Parameters
    ----------
    source : dict
        Source dictionary containing metadata.
    result : ExtractedMetadata
        Result object to update with extracted metadata.
    """
    if not source:
        return

    if not result.title:
        title = source.get("title")
        if title:
            result.title = title

    if not result.authors:
        authors = source.get("authors")
        if authors:
            result.authors = authors if isinstance(authors, list) else [authors]

    if not result.isbn:
        isbn = source.get("isbn")
        if isbn:
            result.isbn = isbn


def extract_metadata(
    history: IngestHistory,
    metadata_hint: dict | None = None,
    fallback_title: str | None = None,
) -> ExtractedMetadata:
    """Extract metadata from hint and history with fallbacks.

    Priority order:
    1. Explicit metadata_hint parameter
    2. History's metadata_hint
    3. History's fetched_metadata
    4. Fallback title (if provided)

    Parameters
    ----------
    history : IngestHistory
        Ingest history record.
    metadata_hint : dict | None
        Optional explicit metadata hint.
    fallback_title : str | None
        Optional fallback title (e.g., from filename).

    Returns
    -------
    ExtractedMetadata
        Extracted metadata with all available fields.
    """
    result = ExtractedMetadata()
    sources = _build_metadata_sources(history, metadata_hint)

    # Extract from sources in priority order
    for source in sources:
        _extract_from_source(source, result)

    # Apply fallback title if still missing
    if not result.title and fallback_title:
        result.title = fallback_title

    return result
