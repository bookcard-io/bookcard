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

"""Ingest stage for fetching and storing external metadata."""

import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlmodel import select

from fundamental.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorSubject,
)
from fundamental.services.library_scanning.data_sources.types import AuthorData
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)

# OpenLibrary covers base URL
OPENLIBRARY_COVERS_BASE = "https://covers.openlibrary.org"


class IngestStage(PipelineStage):
    """Stage that fetches full metadata from external sources.

    Creates/updates AuthorMetadata, AuthorRemoteId, AuthorPhoto, etc.
    Handles incremental updates (only fetch if stale).
    """

    def __init__(self) -> None:
        """Initialize ingest stage."""
        self._progress = 0.0

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "ingest"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def _get_photo_url(self, photo_id: int) -> str:
        """Generate photo URL from OpenLibrary photo ID.

        Parameters
        ----------
        photo_id : int
            OpenLibrary photo ID.

        Returns
        -------
        str
            Photo URL.
        """
        return f"{OPENLIBRARY_COVERS_BASE}/a/id/{photo_id}-L.jpg"

    def _create_or_update_author_metadata(
        self,
        context: PipelineContext,
        author_data: AuthorData,
    ) -> AuthorMetadata:
        """Create or update AuthorMetadata record.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_data : object
            Author data from external source.

        Returns
        -------
        AuthorMetadata
            Created or updated AuthorMetadata record.
        """
        # Check if author metadata already exists
        stmt = select(AuthorMetadata).where(
            AuthorMetadata.openlibrary_key == author_data.key,
        )
        existing = context.session.exec(stmt).first()

        if existing:
            # Update existing record
            existing.name = author_data.name
            existing.personal_name = author_data.personal_name
            existing.fuller_name = author_data.fuller_name
            existing.title = author_data.title
            existing.birth_date = author_data.birth_date
            existing.death_date = author_data.death_date
            existing.entity_type = author_data.entity_type
            existing.biography = author_data.biography
            existing.location = author_data.location
            existing.work_count = author_data.work_count
            existing.ratings_average = author_data.ratings_average
            existing.ratings_count = author_data.ratings_count
            existing.top_work = author_data.top_work
            existing.last_synced_at = datetime.now(UTC)
            existing.updated_at = datetime.now(UTC)

            # Set primary photo URL
            if author_data.photo_ids:
                primary_photo_id = author_data.photo_ids[0]
                existing.photo_url = self._get_photo_url(primary_photo_id)

            author_metadata = existing
        else:
            # Create new record
            photo_url = None
            if author_data.photo_ids:
                primary_photo_id = author_data.photo_ids[0]
                photo_url = self._get_photo_url(primary_photo_id)

            author_metadata = AuthorMetadata(
                openlibrary_key=author_data.key,
                name=author_data.name,
                personal_name=author_data.personal_name,
                fuller_name=author_data.fuller_name,
                title=author_data.title,
                birth_date=author_data.birth_date,
                death_date=author_data.death_date,
                entity_type=author_data.entity_type,
                biography=author_data.biography,
                location=author_data.location,
                photo_url=photo_url,
                work_count=author_data.work_count,
                ratings_average=author_data.ratings_average,
                ratings_count=author_data.ratings_count,
                top_work=author_data.top_work,
                last_synced_at=datetime.now(UTC),
            )

            context.session.add(author_metadata)
            context.session.flush()

        # Update remote IDs
        if author_data.identifiers:
            identifiers_dict = author_data.identifiers.to_dict()
            self._update_remote_ids(context, author_metadata, identifiers_dict)

        # Update photos
        self._update_photos(context, author_metadata, author_data.photo_ids)

        # Update alternate names
        self._update_alternate_names(
            context, author_metadata, author_data.alternate_names
        )

        # Update links
        self._update_links(context, author_metadata, author_data.links)

        # Update subjects
        self._update_subjects(context, author_metadata, author_data.subjects)

        context.session.flush()
        return author_metadata

    def _update_remote_ids(
        self,
        context: PipelineContext,
        author_metadata: AuthorMetadata,
        identifiers_dict: dict[str, str],
    ) -> None:
        """Update remote IDs for author metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_metadata : AuthorMetadata
            Author metadata record.
        identifiers_dict : dict[str, str]
            Dictionary of identifier type to value.
        """
        for id_type, id_value in identifiers_dict.items():
            stmt = select(AuthorRemoteId).where(
                AuthorRemoteId.author_metadata_id == author_metadata.id,
                AuthorRemoteId.identifier_type == id_type,
            )
            existing_id = context.session.exec(stmt).first()

            if existing_id:
                existing_id.identifier_value = id_value
            else:
                remote_id = AuthorRemoteId(
                    author_metadata_id=author_metadata.id,
                    identifier_type=id_type,
                    identifier_value=id_value,
                )
                context.session.add(remote_id)

    def _update_photos(
        self,
        context: PipelineContext,
        author_metadata: AuthorMetadata,
        photo_ids: Sequence[int],
    ) -> None:
        """Update photos for author metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_metadata : AuthorMetadata
            Author metadata record.
        photo_ids : list[int]
            List of photo IDs.
        """
        for idx, photo_id in enumerate(photo_ids):
            stmt = select(AuthorPhoto).where(
                AuthorPhoto.author_metadata_id == author_metadata.id,
                AuthorPhoto.openlibrary_photo_id == photo_id,
            )
            existing_photo = context.session.exec(stmt).first()

            if not existing_photo:
                photo = AuthorPhoto(
                    author_metadata_id=author_metadata.id,
                    openlibrary_photo_id=photo_id,
                    photo_url=self._get_photo_url(photo_id),
                    is_primary=(idx == 0),
                    order=idx,
                )
                context.session.add(photo)

    def _update_alternate_names(
        self,
        context: PipelineContext,
        author_metadata: AuthorMetadata,
        alternate_names: Sequence[str],
    ) -> None:
        """Update alternate names for author metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_metadata : AuthorMetadata
            Author metadata record.
        alternate_names : list[str]
            List of alternate names.
        """
        for alt_name in alternate_names:
            stmt = select(AuthorAlternateName).where(
                AuthorAlternateName.author_metadata_id == author_metadata.id,
                AuthorAlternateName.name == alt_name,
            )
            existing_alt = context.session.exec(stmt).first()

            if not existing_alt:
                alt = AuthorAlternateName(
                    author_metadata_id=author_metadata.id,
                    name=alt_name,
                )
                context.session.add(alt)

    def _update_links(
        self,
        context: PipelineContext,
        author_metadata: AuthorMetadata,
        links: Sequence[dict[str, str]],
    ) -> None:
        """Update links for author metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_metadata : AuthorMetadata
            Author metadata record.
        links : list[dict[str, Any]]
            List of link dictionaries.
        """
        for link_data in links:
            stmt = select(AuthorLink).where(
                AuthorLink.author_metadata_id == author_metadata.id,
                AuthorLink.url == link_data.get("url", ""),
            )
            existing_link = context.session.exec(stmt).first()

            if not existing_link:
                link = AuthorLink(
                    author_metadata_id=author_metadata.id,
                    title=link_data.get("title", ""),
                    url=link_data.get("url", ""),
                    link_type=link_data.get("type"),
                )
                context.session.add(link)

    def _update_subjects(
        self,
        context: PipelineContext,
        author_metadata: AuthorMetadata,
        subjects: Sequence[str],
    ) -> None:
        """Update subjects for author metadata.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        author_metadata : AuthorMetadata
            Author metadata record.
        subjects : list[str]
            List of subject names.
        """
        for rank, subject_name in enumerate(subjects):
            stmt = select(AuthorSubject).where(
                AuthorSubject.author_metadata_id == author_metadata.id,
                AuthorSubject.subject_name == subject_name,
            )
            existing_subject = context.session.exec(stmt).first()

            if not existing_subject:
                subject = AuthorSubject(
                    author_metadata_id=author_metadata.id,
                    subject_name=subject_name,
                    rank=rank,
                )
                context.session.add(subject)

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the ingest stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with match results.

        Returns
        -------
        StageResult
            Result with ingested metadata counts.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Ingest cancelled")

        try:
            match_results = context.match_results
            total_matches = len(match_results)

            if total_matches == 0:
                return StageResult(
                    success=True,
                    message="No matches to ingest",
                    stats={"ingested": 0},
                )

            ingested_count = 0
            failed_count = 0

            for idx, match_result in enumerate(match_results):
                if context.check_cancelled():
                    return StageResult(success=False, message="Ingest cancelled")

                try:
                    # Fetch full author data from external source
                    author_key = match_result.matched_entity.key
                    full_author_data = context.data_source.get_author(author_key)

                    if full_author_data:
                        # Create or update author metadata
                        self._create_or_update_author_metadata(
                            context,
                            full_author_data,
                        )
                        ingested_count += 1
                    else:
                        failed_count += 1
                        logger.warning(
                            "Could not fetch full author data for key: %s",
                            author_key,
                        )

                except Exception:
                    failed_count += 1
                    logger.exception(
                        "Error ingesting author %s",
                        match_result.matched_entity.key,
                    )

                # Update progress with metadata
                self._progress = (idx + 1) / total_matches
                metadata = {
                    "current_item": match_result.matched_entity.name,
                    "current_index": idx + 1,
                    "total_items": total_matches,
                    "ingested": ingested_count,
                    "failed": failed_count,
                }
                context.update_progress(self._progress, metadata)

            # Commit all changes
            context.session.commit()

            stats = {
                "ingested": ingested_count,
                "failed": failed_count,
                "total": total_matches,
            }

            logger.info(
                "Ingested %d/%d authors in library %d",
                ingested_count,
                total_matches,
                context.library_id,
            )

            return StageResult(
                success=True,
                message=f"Ingested {ingested_count}/{total_matches} authors",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in ingest stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Ingest failed: {e}",
            )
