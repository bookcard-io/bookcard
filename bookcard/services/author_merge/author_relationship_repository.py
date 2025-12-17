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

"""Repository for author relationship operations.

Follows SRP by focusing solely on relationship data access,
including similarities, works, and related entities.
"""

import logging
from contextlib import suppress
from pathlib import Path

from sqlmodel import Session, func, select

from bookcard.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorSimilarity,
    AuthorUserMetadata,
    AuthorUserPhoto,
    AuthorWork,
    WorkSubject,
)
from bookcard.services.author_merge.value_objects import RelationshipCounts

logger = logging.getLogger(__name__)


class AuthorRelationshipRepository:
    """Repository for author relationship operations.

    Handles all database operations related to author relationships,
    including similarities, works, and metadata counts.
    """

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize relationship repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self._session = session

    def get_relationship_counts(self, author_id: int) -> RelationshipCounts:
        """Get relationship counts for an author.

        Parameters
        ----------
        author_id : int
            Author metadata ID.

        Returns
        -------
        RelationshipCounts
            Relationship counts for the author.
        """
        # Count alternate names
        alt_names_count = (
            self._session.exec(
                select(func.count(AuthorAlternateName.id)).where(
                    AuthorAlternateName.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count remote IDs
        remote_ids_count = (
            self._session.exec(
                select(func.count(AuthorRemoteId.id)).where(
                    AuthorRemoteId.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count photos
        photos_count = (
            self._session.exec(
                select(func.count(AuthorPhoto.id)).where(
                    AuthorPhoto.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count links
        links_count = (
            self._session.exec(
                select(func.count(AuthorLink.id)).where(
                    AuthorLink.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count works
        works_count = (
            self._session.exec(
                select(func.count(AuthorWork.id)).where(
                    AuthorWork.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count work subjects
        subjects_count = 0
        if works_count > 0:
            subjects_count = (
                self._session.exec(
                    select(func.count(WorkSubject.id))
                    .join(AuthorWork, WorkSubject.author_work_id == AuthorWork.id)
                    .where(AuthorWork.author_metadata_id == author_id)
                ).one()
                or 0
            )

        # Count similarities (both directions)
        similarities_count = (
            self._session.exec(
                select(func.count(AuthorSimilarity.id)).where(
                    (AuthorSimilarity.author1_id == author_id)
                    | (AuthorSimilarity.author2_id == author_id)
                )
            ).one()
            or 0
        )

        # Count user metadata
        user_metadata_count = (
            self._session.exec(
                select(func.count(AuthorUserMetadata.id)).where(
                    AuthorUserMetadata.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        # Count user photos
        user_photos_count = (
            self._session.exec(
                select(func.count(AuthorUserPhoto.id)).where(
                    AuthorUserPhoto.author_metadata_id == author_id
                )
            ).one()
            or 0
        )

        return RelationshipCounts(
            alternate_names=alt_names_count,
            remote_ids=remote_ids_count,
            photos=photos_count,
            links=links_count,
            works=works_count,
            work_subjects=subjects_count,
            similarities=similarities_count,
            user_metadata=user_metadata_count,
            user_photos=user_photos_count,
        )

    def update_similarities_for_merge(
        self,
        keep_author_id: int,
        merge_author_id: int,
    ) -> None:
        """Update AuthorSimilarity records when merging authors.

        Transfers all similarities from merge_author to keep_author,
        handling duplicates and self-similarities.

        Parameters
        ----------
        keep_author_id : int
            Author ID to keep.
        merge_author_id : int
            Author ID being merged (will be deleted).
        """
        logger.debug(
            "Updating similarities: keep_author_id=%s, merge_author_id=%s",
            keep_author_id,
            merge_author_id,
        )

        # Track similarities we're updating to avoid duplicates within this batch
        pending_updates: set[tuple[int, int]] = set()

        # Process similarities where merge is author1
        self._process_similarities_as_author1(
            keep_author_id, merge_author_id, pending_updates
        )

        # Process similarities where merge is author2
        self._process_similarities_as_author2(
            keep_author_id, merge_author_id, pending_updates
        )

        # Final flush to ensure all updates are persisted
        self._session.flush()

    def _process_similarities_as_author1(
        self,
        keep_author_id: int,
        merge_author_id: int,
        pending_updates: set[tuple[int, int]],
    ) -> None:
        """Process similarities where merge author is author1.

        Parameters
        ----------
        keep_author_id : int
            Author ID to keep.
        merge_author_id : int
            Author ID being merged.
        pending_updates : set[tuple[int, int]]
            Set of pending updates to track duplicates.
        """
        similarity_stmt = select(AuthorSimilarity).where(
            AuthorSimilarity.author1_id == merge_author_id
        )
        similarities = list(self._session.exec(similarity_stmt).all())
        logger.debug(
            "Found %d similarities where merge_author is author1",
            len(similarities),
        )

        for sim in similarities:
            if sim.author2_id == keep_author_id:
                # Self-similarity after merge - delete it
                self._session.delete(sim)
            elif not sim.author2_id:
                # Invalid similarity with null author2_id - delete it
                self._session.delete(sim)
            else:
                self._update_or_delete_similarity(
                    sim,
                    keep_author_id,
                    sim.author2_id,
                    "author1_id",
                    pending_updates,
                )

    def _process_similarities_as_author2(
        self,
        keep_author_id: int,
        merge_author_id: int,
        pending_updates: set[tuple[int, int]],
    ) -> None:
        """Process similarities where merge author is author2.

        Parameters
        ----------
        keep_author_id : int
            Author ID to keep.
        merge_author_id : int
            Author ID being merged.
        pending_updates : set[tuple[int, int]]
            Set of pending updates to track duplicates.
        """
        similarity_stmt = select(AuthorSimilarity).where(
            AuthorSimilarity.author2_id == merge_author_id
        )
        similarities = list(self._session.exec(similarity_stmt).all())
        logger.debug(
            "Found %d similarities where merge_author is author2",
            len(similarities),
        )

        for sim in similarities:
            if sim.author1_id == keep_author_id:
                # Self-similarity after merge - delete it
                self._session.delete(sim)
            elif not sim.author1_id:
                # Invalid similarity with null author1_id - delete it
                self._session.delete(sim)
            else:
                self._update_or_delete_similarity(
                    sim,
                    keep_author_id,
                    sim.author1_id,
                    "author2_id",
                    pending_updates,
                )

    def _update_or_delete_similarity(
        self,
        sim: AuthorSimilarity,
        keep_author_id: int,
        other_author_id: int,
        field_to_update: str,
        pending_updates: set[tuple[int, int]],
    ) -> None:
        """Update or delete a similarity record.

        Parameters
        ----------
        sim : AuthorSimilarity
            Similarity record to update or delete.
        keep_author_id : int
            Author ID to keep.
        other_author_id : int
            Other author ID in the similarity.
        field_to_update : str
            Field name to update ("author1_id" or "author2_id").
        pending_updates : set[tuple[int, int]]
            Set of pending updates to track duplicates.
        """
        # Check both directions: (keep, other) and (other, keep)
        target_pair_forward = (keep_author_id, other_author_id)
        target_pair_reverse = (other_author_id, keep_author_id)

        existing_forward = self._session.exec(
            select(AuthorSimilarity).where(
                AuthorSimilarity.author1_id == keep_author_id,
                AuthorSimilarity.author2_id == other_author_id,
            )
        ).first()
        existing_reverse = self._session.exec(
            select(AuthorSimilarity).where(
                AuthorSimilarity.author1_id == other_author_id,
                AuthorSimilarity.author2_id == keep_author_id,
            )
        ).first()

        # Check if we're already updating to this pair in this batch
        if (
            existing_forward
            or existing_reverse
            or target_pair_forward in pending_updates
            or target_pair_reverse in pending_updates
        ):
            # Duplicate similarity - delete the merge author's similarity
            self._session.delete(sim)
        else:
            # Update to point to keep author
            setattr(sim, field_to_update, keep_author_id)
            pending_updates.add(target_pair_forward)
            # Flush immediately to make this update visible for subsequent checks
            # This prevents duplicate key violations when multiple merge authors
            # have similarities to the same other author
            self._session.flush()
            # Expunge from session to prevent SQLAlchemy from trying to nullify
            # the foreign key when merge_author is deleted
            self._session.expunge(sim)

    def delete_author_works(self, author_id: int) -> None:
        """Delete all AuthorWork records for an author.

        This prevents SQLAlchemy from trying to nullify foreign keys.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        """
        remaining_works = list(
            self._session.exec(
                select(AuthorWork).where(AuthorWork.author_metadata_id == author_id)
            ).all()
        )

        for work in remaining_works:
            # Delete all subjects associated with this work first
            if work.id:
                subjects = list(
                    self._session.exec(
                        select(WorkSubject).where(WorkSubject.author_work_id == work.id)
                    ).all()
                )
                for subject in subjects:
                    self._session.delete(subject)

            # Delete the work
            self._session.delete(work)

        if remaining_works:
            self._session.flush()

    def cleanup_remaining_similarities(self, author_id: int) -> None:
        """Delete any remaining similarities that reference an author.

        This is a safety check in case update_similarities_for_merge missed some
        or if there were concurrent updates.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        """
        remaining_similarities1 = list(
            self._session.exec(
                select(AuthorSimilarity).where(AuthorSimilarity.author1_id == author_id)
            ).all()
        )
        remaining_similarities2 = list(
            self._session.exec(
                select(AuthorSimilarity).where(AuthorSimilarity.author2_id == author_id)
            ).all()
        )

        for sim in remaining_similarities1:
            self._session.delete(sim)

        for sim in remaining_similarities2:
            self._session.delete(sim)

        if remaining_similarities1 or remaining_similarities2:
            self._session.flush()

    def delete_author_user_photos(
        self, author_id: int, data_directory: str | Path | None = None
    ) -> None:
        """Delete all AuthorUserPhoto records and their files for an author.

        This prevents SQLAlchemy from trying to nullify foreign keys.
        Also deletes the actual photo files from the filesystem.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        data_directory : str | Path | None
            Data directory path. If provided, will also delete photo files.
            If None, only deletes database records.
        """
        user_photos = list(
            self._session.exec(
                select(AuthorUserPhoto).where(
                    AuthorUserPhoto.author_metadata_id == author_id
                )
            ).all()
        )

        # Delete files from filesystem if data_directory is provided
        if data_directory is not None:
            data_dir = Path(data_directory)
            for photo in user_photos:
                if photo.file_path:
                    photo_path = data_dir / photo.file_path
                    if photo_path.exists():
                        with suppress(OSError):
                            photo_path.unlink()
                            logger.debug(
                                "Deleted photo file: %s for author %s",
                                photo_path,
                                author_id,
                            )

        # Delete database records
        for photo in user_photos:
            self._session.delete(photo)

        if user_photos:
            self._session.flush()

    def delete_author_user_metadata(self, author_id: int) -> None:
        """Delete all AuthorUserMetadata records for an author.

        This prevents SQLAlchemy from trying to nullify foreign keys.

        Parameters
        ----------
        author_id : int
            Author metadata ID.
        """
        user_metadata = list(
            self._session.exec(
                select(AuthorUserMetadata).where(
                    AuthorUserMetadata.author_metadata_id == author_id
                )
            ).all()
        )

        for metadata in user_metadata:
            self._session.delete(metadata)

        if user_metadata:
            self._session.flush()
