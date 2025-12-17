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

"""Repositories for library scanning operations.

This module contains data access components used across multiple stages
of the scanning pipeline (match, link, ingest) to avoid circular imports.
"""

import logging
from dataclasses import dataclass

from sqlmodel import Session, select

from bookcard.models.author_metadata import AuthorMapping, AuthorMetadata

logger = logging.getLogger(__name__)


# ============================================================================
# Value Objects
# ============================================================================


@dataclass
class MappingData:
    """Value object for mapping data.

    Parameters
    ----------
    library_id : int
        Library identifier.
    calibre_author_id : int
        Calibre author ID.
    author_metadata_id : int
        Author metadata ID.
    confidence_score : float | None
        Matching confidence score.
    matched_by : str | None
        How the match was made.
    """

    library_id: int
    calibre_author_id: int
    author_metadata_id: int
    confidence_score: float | None
    matched_by: str | None


# ============================================================================
# Repository Layer
# ============================================================================


class AuthorMappingRepository:
    """Repository for AuthorMapping operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_calibre_author_id(self, calibre_author_id: int) -> AuthorMapping | None:
        """Find mapping by Calibre author ID.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID.

        Returns
        -------
        AuthorMapping | None
            Mapping if found, None otherwise.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.calibre_author_id == calibre_author_id
        )
        return self.session.exec(stmt).first()

    def find_by_calibre_author_id_and_library(
        self, calibre_author_id: int, library_id: int
    ) -> AuthorMapping | None:
        """Find mapping by Calibre author ID and library ID.

        Parameters
        ----------
        calibre_author_id : int
            Calibre author ID.
        library_id : int
            Library ID.

        Returns
        -------
        AuthorMapping | None
            Mapping if found, None otherwise.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.calibre_author_id == calibre_author_id,
            AuthorMapping.library_id == library_id,
        )
        return self.session.exec(stmt).first()

    def create(self, mapping_data: MappingData) -> AuthorMapping:
        """Create new mapping.

        Parameters
        ----------
        mapping_data : MappingData
            Mapping data.

        Returns
        -------
        AuthorMapping
            Created mapping record.
        """
        mapping = AuthorMapping(
            library_id=mapping_data.library_id,
            calibre_author_id=mapping_data.calibre_author_id,
            author_metadata_id=mapping_data.author_metadata_id,
            confidence_score=mapping_data.confidence_score,
            matched_by=mapping_data.matched_by,
        )
        self.session.add(mapping)
        return mapping

    def update(
        self,
        existing: AuthorMapping,
        mapping_data: MappingData,
    ) -> AuthorMapping:
        """Update an existing mapping record.

        Parameters
        ----------
        existing : AuthorMapping
            Existing mapping record to update.
        mapping_data : MappingData
            New mapping data values.

        Returns
        -------
        AuthorMapping
            Updated mapping record.
        """
        existing.library_id = mapping_data.library_id
        existing.calibre_author_id = mapping_data.calibre_author_id
        existing.author_metadata_id = mapping_data.author_metadata_id
        existing.confidence_score = mapping_data.confidence_score
        existing.matched_by = mapping_data.matched_by
        return existing

    def delete_mappings_for_metadata_exclude_author(
        self, author_metadata_id: int, exclude_calibre_author_id: int
    ) -> int:
        """Delete mappings for a metadata ID, excluding a specific Calibre author.

        Parameters
        ----------
        author_metadata_id : int
            Author metadata ID.
        exclude_calibre_author_id : int
            Calibre author ID to exclude from deletion.

        Returns
        -------
        int
            Number of deleted mappings.
        """
        stmt = select(AuthorMapping).where(
            AuthorMapping.author_metadata_id == author_metadata_id,
            AuthorMapping.calibre_author_id != exclude_calibre_author_id,
        )
        mappings = self.session.exec(stmt).all()
        count = len(mappings)
        for mapping in mappings:
            self.session.delete(mapping)
        return count


class AuthorMetadataRepository:
    """Repository for AuthorMetadata operations."""

    def __init__(self, session: Session) -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def find_by_openlibrary_key(self, key: str) -> AuthorMetadata | None:
        """Find author metadata by OpenLibrary key.

        Parameters
        ----------
        key : str
            OpenLibrary author key.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        # Normalize key to OpenLibrary convention: ensure /authors/ prefix
        if not key.startswith("/authors/"):
            normalized_key = f"/authors/{key.replace('authors/', '')}"
        else:
            normalized_key = key

        logger.debug(
            "Looking up AuthorMetadata with key: %s (normalized: %s)",
            key,
            normalized_key,
        )
        stmt = select(AuthorMetadata).where(
            AuthorMetadata.openlibrary_key == normalized_key
        )
        result = self.session.exec(stmt).first()
        if result:
            logger.debug(
                "Found AuthorMetadata: ID=%s, key=%s, name=%s",
                result.id,
                result.openlibrary_key,
                result.name,
            )
        else:
            logger.debug("AuthorMetadata not found for key: %s", key)
        return result
