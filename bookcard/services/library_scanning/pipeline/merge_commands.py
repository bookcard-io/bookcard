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

"""Merge commands for author record deduplication.

Uses Command pattern to separate merge operations into focused, testable units.
Each command handles a specific aspect of merging duplicate author records.
"""

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy.exc import IntegrityError
from sqlmodel import select

if TYPE_CHECKING:
    from bookcard.services.library_scanning.pipeline.duplicate_detector import (
        DuplicatePair,
    )

from bookcard.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorSimilarity,
    AuthorWork,
    WorkSubject,
)
from bookcard.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class MergeCommand(ABC):
    """Base class for merge operations.

    Each command handles a specific aspect of merging duplicate author records.
    Follows Command pattern for separation of concerns and testability.
    """

    @abstractmethod
    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Execute the merge operation.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep (higher quality).
        merge : AuthorMetadata
            Record to merge into keep.
        """


class MergeAlternateNames(MergeCommand):
    """Merge alternate names from source to target."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge alternate names.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        existing_names = {alt.name for alt in keep.alternate_names}
        for alt_name in merge.alternate_names:
            if alt_name.name not in existing_names:
                new_alt = AuthorAlternateName(
                    author_metadata_id=keep.id,
                    name=alt_name.name,
                )
                context.session.add(new_alt)
                existing_names.add(alt_name.name)

        # Remove all alternate names from the merged author to avoid leaving
        # rows that reference a soon-to-be-deleted AuthorMetadata record.
        for alt_name in list(merge.alternate_names):
            context.session.delete(alt_name)


class MergeRemoteIds(MergeCommand):
    """Merge remote IDs from source to target."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge remote IDs.

        The unique constraint is on (author_metadata_id, identifier_type),
        so we can only have one remote ID of each type per author.
        We check if the identifier_type already exists for the keep author,
        and only add if it doesn't exist.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        # Track existing identifier types for the keep author
        # Unique constraint is on (author_metadata_id, identifier_type)
        existing_types = {rid.identifier_type for rid in keep.remote_ids}

        # Also track existing (type, value) pairs to avoid exact duplicates
        existing_pairs = {
            (rid.identifier_type, rid.identifier_value) for rid in keep.remote_ids
        }

        for remote_id in merge.remote_ids:
            # Skip if this identifier type already exists for keep author
            # (unique constraint: one per type per author)
            if remote_id.identifier_type in existing_types:
                logger.debug(
                    "Skipping remote ID %s=%s for author %s: type already exists",
                    remote_id.identifier_type,
                    remote_id.identifier_value,
                    keep.id,
                )
                continue

            # Skip if exact duplicate (type + value) already exists
            key = (remote_id.identifier_type, remote_id.identifier_value)
            if key in existing_pairs:
                logger.debug(
                    "Skipping duplicate remote ID %s=%s for author %s",
                    remote_id.identifier_type,
                    remote_id.identifier_value,
                    keep.id,
                )
                continue

            # Add new remote ID
            try:
                new_rid = AuthorRemoteId(
                    author_metadata_id=keep.id,
                    identifier_type=remote_id.identifier_type,
                    identifier_value=remote_id.identifier_value,
                )
                context.session.add(new_rid)
                # Flush to check for constraint violations immediately
                context.session.flush()
                existing_types.add(remote_id.identifier_type)
                existing_pairs.add(key)
            except IntegrityError as e:
                # Handle unique constraint violations gracefully
                # This can happen if the identifier_type was added between our check and the insert
                # (e.g., by another process or due to race conditions)
                logger.warning(
                    "Skipping remote ID %s=%s for author %s: constraint violation (likely duplicate type): %s",
                    remote_id.identifier_type,
                    remote_id.identifier_value,
                    keep.id,
                    e,
                )
                # Rollback the session to clear the error state
                context.session.rollback()
                # Refresh the keep author to get updated remote_ids
                context.session.refresh(keep)
                # Update our tracking sets
                existing_types = {rid.identifier_type for rid in keep.remote_ids}
                existing_pairs = {
                    (rid.identifier_type, rid.identifier_value)
                    for rid in keep.remote_ids
                }
                continue

        # Remove all remote IDs from the merged author after copying to keep.
        for remote_id in list(merge.remote_ids):
            context.session.delete(remote_id)


class MergePhotos(MergeCommand):
    """Merge author photos."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge photos.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        existing_photo_ids = {
            photo.openlibrary_photo_id
            for photo in keep.photos
            if photo.openlibrary_photo_id
        }
        existing_photo_urls = {
            photo.photo_url for photo in keep.photos if photo.photo_url
        }

        for photo in merge.photos:
            if self._photo_exists(photo, existing_photo_ids, existing_photo_urls):
                continue

            new_photo = AuthorPhoto(
                author_metadata_id=keep.id,
                openlibrary_photo_id=photo.openlibrary_photo_id,
                photo_url=photo.photo_url,
                is_primary=False,  # Keep existing primary
            )
            context.session.add(new_photo)
            self._update_existing_sets(photo, existing_photo_ids, existing_photo_urls)

        # Remove all photos from the merged author after copying to keep.
        for photo in list(merge.photos):
            context.session.delete(photo)

    def _photo_exists(
        self,
        photo: AuthorPhoto,
        existing_ids: set[int],
        existing_urls: set[str],
    ) -> bool:
        """Check if photo already exists.

        Parameters
        ----------
        photo : AuthorPhoto
            Photo to check.
        existing_ids : set[int]
            Set of existing photo IDs.
        existing_urls : set[str]
            Set of existing photo URLs.

        Returns
        -------
        bool
            True if photo exists, False otherwise.
        """
        return bool(
            (photo.openlibrary_photo_id and photo.openlibrary_photo_id in existing_ids)
            or (photo.photo_url and photo.photo_url in existing_urls)
        )

    def _update_existing_sets(
        self,
        photo: AuthorPhoto,
        existing_ids: set[int],
        existing_urls: set[str],
    ) -> None:
        """Update existing sets with photo data.

        Parameters
        ----------
        photo : AuthorPhoto
            Photo that was added.
        existing_ids : set[int]
            Set of existing photo IDs to update.
        existing_urls : set[str]
            Set of existing photo URLs to update.
        """
        if photo.openlibrary_photo_id:
            existing_ids.add(photo.openlibrary_photo_id)
        if photo.photo_url:
            existing_urls.add(photo.photo_url)


class MergeLinks(MergeCommand):
    """Merge author links."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge links.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        existing_link_urls = {link.url for link in keep.links}
        for link in merge.links:
            if link.url not in existing_link_urls:
                new_link = AuthorLink(
                    author_metadata_id=keep.id,
                    title=link.title,
                    url=link.url,
                    link_type=link.link_type,
                )
                context.session.add(new_link)
                existing_link_urls.add(link.url)

        # Remove all links from the merged author after copying to keep.
        for link in list(merge.links):
            context.session.delete(link)


class MergeWorks(MergeCommand):
    """Merge author works."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge works.

        Subjects are linked to works, so they'll be preserved with works.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        logger.debug(
            "MergeWorks: starting for keep.id=%s, merge.id=%s",
            getattr(keep, "id", None),
            getattr(merge, "id", None),
        )

        # Decide which author instance will own the final set of works.
        # Prefer the persisted "keep" record; fall back to "merge" if needed.
        if keep.id is not None:
            final_author = keep
            source_author = merge
        elif merge.id is not None:
            final_author = merge
            source_author = keep
        else:
            # Neither author has an ID, so there are no persisted works to merge.
            return

        existing_work_keys = {w.work_key for w in final_author.works}

        logger.debug(
            "MergeWorks: final_author.id=%s initially has %d works (ids=%s)",
            getattr(final_author, "id", None),
            len(final_author.works),
            [w.id for w in final_author.works],
        )
        logger.debug(
            "MergeWorks: source_author.id=%s initially has %d works (ids=%s)",
            getattr(source_author, "id", None),
            len(source_author.works),
            [w.id for w in source_author.works],
        )

        # Use relationship-based operations so SQLAlchemy properly tracks
        # parent/child associations and does not attempt to null out foreign keys
        # when the merged author record is deleted.
        # Use no_autoflush to prevent premature flushes that could cause constraint violations
        with context.session.no_autoflush:
            for work in list(source_author.works):
                if work.work_key in existing_work_keys:
                    # Duplicate work for the merged author - remove it explicitly.
                    # First, delete all subjects associated with this work to avoid
                    # NOT NULL constraint violations on work_subjects.author_work_id
                    if work.id is not None:
                        # Load subjects if not already loaded
                        if not hasattr(work, "subjects") or work.subjects is None:
                            # Query subjects for this work
                            subjects_stmt = select(WorkSubject).where(
                                WorkSubject.author_work_id == work.id
                            )
                            subjects = list(context.session.exec(subjects_stmt).all())
                        else:
                            subjects = list(work.subjects)

                        # Delete all subjects before deleting the work
                        for subject in subjects:
                            logger.debug(
                                "MergeWorks: deleting subject id=%s (%s) from duplicate work id=%s",
                                subject.id,
                                subject.subject_name,
                                work.id,
                            )
                            context.session.delete(subject)

                    logger.debug(
                        "MergeWorks: deleting duplicate work id=%s key=%s from "
                        "source_author.id=%s",
                        work.id,
                        work.work_key,
                        getattr(source_author, "id", None),
                    )
                    context.session.delete(work)
                else:
                    logger.debug(
                        "MergeWorks: moving work id=%s key=%s from source_author.id=%s "
                        "to final_author.id=%s",
                        work.id,
                        work.work_key,
                        getattr(source_author, "id", None),
                        getattr(final_author, "id", None),
                    )
                    # Move work to final author by explicitly updating author_metadata_id
                    # This preserves the work's ID and all its subjects
                    # (subjects' author_work_id doesn't change, only work's author_metadata_id changes)
                    if final_author.id is not None:
                        work.author_metadata_id = final_author.id
                        # Add to relationship for proper tracking
                        final_author.works.append(work)
                    existing_work_keys.add(work.work_key)

        logger.debug(
            "MergeWorks: after merge, final_author.id=%s has %d works (ids=%s); "
            "source_author.id=%s has %d works (ids=%s)",
            getattr(final_author, "id", None),
            len(final_author.works),
            [w.id for w in final_author.works],
            getattr(source_author, "id", None),
            len(source_author.works),
            [w.id for w in source_author.works],
        )


class MergeFields(MergeCommand):
    """Merge scalar fields, preferring non-null values."""

    FIELDS_TO_MERGE: ClassVar[list[str]] = [
        "biography",
        "location",
        "photo_url",
        "personal_name",
        "fuller_name",
        "birth_date",
        "death_date",
        "title",
        "top_work",
    ]

    NUMERIC_FIELDS: ClassVar[list[tuple[str, Callable[[list[float]], float]]]] = [
        ("work_count", max),
        ("ratings_count", max),
        ("ratings_average", max),
    ]

    def execute(
        self,
        _context: PipelineContext,
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge fields.

        Parameters
        ----------
        _context : PipelineContext
            Pipeline context with database session (unused).
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        # Merge text fields (prefer non-null)
        for field in self.FIELDS_TO_MERGE:
            if not getattr(keep, field) and getattr(merge, field):
                setattr(keep, field, getattr(merge, field))

        # Merge numeric fields (prefer higher values)
        for field, strategy in self.NUMERIC_FIELDS:
            merge_val = getattr(merge, field)
            keep_val = getattr(keep, field)
            if merge_val is not None and (
                keep_val is None or strategy([merge_val, keep_val]) == merge_val
            ):
                setattr(keep, field, merge_val)


class UpdateReferences(MergeCommand):
    """Update all references from merge to keep."""

    def execute(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Update references.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        self._update_mappings(context, keep, merge)
        self._update_similarities(context, keep, merge)

    def _update_mappings(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Update AuthorMapping records.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        mapping_stmt = select(AuthorMapping).where(
            AuthorMapping.author_metadata_id == merge.id
        )
        for mapping in context.session.exec(mapping_stmt).all():
            mapping.author_metadata_id = keep.id
            mapping.updated_at = datetime.now(UTC)
            logger.debug(
                "Updated AuthorMapping %s to point to merged record %s",
                mapping.id,
                keep.id,
            )

    def _update_similarities(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Update AuthorSimilarity records.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge from.
        """
        # Similarities where merge is author1
        similarity_stmt1 = select(AuthorSimilarity).where(
            AuthorSimilarity.author1_id == merge.id
        )
        for sim in context.session.exec(similarity_stmt1).all():
            if sim.author2_id == keep.id:
                # Self-similarity after merge - delete it
                context.session.delete(sim)
            else:
                sim.author1_id = keep.id

        # Similarities where merge is author2
        similarity_stmt2 = select(AuthorSimilarity).where(
            AuthorSimilarity.author2_id == merge.id
        )
        for sim in context.session.exec(similarity_stmt2).all():
            if sim.author1_id == keep.id:
                # Self-similarity after merge - delete it
                context.session.delete(sim)
            else:
                sim.author2_id = keep.id


class AuthorMerger:
    """Orchestrates the author merge process.

    Uses Command pattern to execute merge operations in sequence.
    Each command handles a specific aspect of the merge.
    """

    def __init__(self) -> None:
        """Initialize author merger with merge commands."""
        self.commands: list[MergeCommand] = [
            MergeAlternateNames(),
            MergeRemoteIds(),
            MergePhotos(),
            MergeLinks(),
            MergeWorks(),
            MergeFields(),
            UpdateReferences(),
        ]

    def _ensure_keep_has_library_mapping(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> tuple[AuthorMetadata, AuthorMetadata]:
        """Ensure keep author has library mapping if possible.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep (higher quality).
        merge : AuthorMetadata
            Record to merge into keep (will be deleted).

        Returns
        -------
        tuple[AuthorMetadata, AuthorMetadata]
            Tuple of (keep, merge) - may be swapped if merge has mapping.
        """
        # Prefer keeping the author that is already mapped to the current library.
        # This avoids "losing" matched books in the library when the canonical
        # AuthorMetadata record changes.
        if keep.id is None or merge.id is None:
            return keep, merge

        def _has_library_mapping(author_id: int) -> bool:
            stmt = select(AuthorMapping).where(
                AuthorMapping.author_metadata_id == author_id,
                AuthorMapping.library_id == context.library_id,
            )
            return context.session.exec(stmt).first() is not None

        keep_mapped = _has_library_mapping(keep.id)
        merge_mapped = _has_library_mapping(merge.id)

        # If exactly one of the authors is mapped to this library, prefer it
        # as the "keep" record, regardless of the detector's scoring.
        if merge_mapped and not keep_mapped:
            logger.debug(
                "AuthorMerger.merge: swapping keep/merge to preserve library "
                "mappings for library_id=%s (keep_id=%s had no mappings, "
                "merge_id=%s had mappings)",
                context.library_id,
                keep.id,
                merge.id,
            )
            return merge, keep

        return keep, merge

    def _log_work_counts(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> tuple[list[int], list[int]]:
        """Log initial work counts for both authors.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep.
        merge : AuthorMetadata
            Record to merge.

        Returns
        -------
        tuple[list[int], list[int]]
            Tuple of (keep_work_ids, merge_work_ids).
        """
        keep_work_ids: list[int] = []
        merge_work_ids: list[int] = []
        if keep.id is not None:
            keep_works = context.session.exec(
                select(AuthorWork).where(AuthorWork.author_metadata_id == keep.id)
            ).all()
            keep_work_ids = [w.id for w in keep_works]
        if merge.id is not None:
            merge_works = context.session.exec(
                select(AuthorWork).where(AuthorWork.author_metadata_id == merge.id)
            ).all()
            merge_work_ids = [w.id for w in merge_works]

        logger.debug(
            "AuthorMerger.merge: before commands, keep.id=%s has %d works (ids=%s); "
            "merge.id=%s has %d works (ids=%s)",
            getattr(keep, "id", None),
            len(keep_work_ids),
            keep_work_ids,
            getattr(merge, "id", None),
            len(merge_work_ids),
            merge_work_ids,
        )
        return keep_work_ids, merge_work_ids

    def _cleanup_remaining_works(
        self,
        context: "PipelineContext",
        merge: AuthorMetadata,
    ) -> None:
        """Clean up any remaining works that reference merged author.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        merge : AuthorMetadata
            Record being merged (will be deleted).
        """
        if merge.id is None:
            return

        remaining_work_stmt = select(AuthorWork).where(
            AuthorWork.author_metadata_id == merge.id
        )
        remaining_works = context.session.exec(remaining_work_stmt).all()
        if remaining_works:
            logger.error(
                "AuthorMerger.merge: %d AuthorWork rows still reference merged "
                "author id=%s after MergeWorks. Deleting them to maintain "
                "integrity. work_ids=%s, work_keys=%s",
                len(remaining_works),
                merge.id,
                [w.id for w in remaining_works],
                [w.work_key for w in remaining_works],
            )
            # Delete subjects first to avoid NOT NULL constraint violations
            with context.session.no_autoflush:
                for work in remaining_works:
                    if work.id is not None:
                        # Delete all subjects for this work
                        subjects_stmt = select(WorkSubject).where(
                            WorkSubject.author_work_id == work.id
                        )
                        subjects = list(context.session.exec(subjects_stmt).all())
                        for subject in subjects:
                            logger.debug(
                                "AuthorMerger._cleanup_remaining_works: deleting subject id=%s (%s) from work id=%s",
                                subject.id,
                                subject.subject_name,
                                work.id,
                            )
                            context.session.delete(subject)
                    # Then delete the work
                    context.session.delete(work)

    def merge(
        self,
        context: "PipelineContext",
        keep: AuthorMetadata,
        merge: AuthorMetadata,
    ) -> None:
        """Merge duplicate author records.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        keep : AuthorMetadata
            Record to keep (higher quality).
        merge : AuthorMetadata
            Record to merge into keep (will be deleted).
        """
        # Ensure keep has library mapping if possible
        keep, merge = self._ensure_keep_has_library_mapping(context, keep, merge)

        logger.info(
            "Merging duplicate authors: '%s' (%s, id=%s) into '%s' (%s, id=%s)",
            merge.name,
            merge.openlibrary_key,
            getattr(merge, "id", None),
            keep.name,
            keep.openlibrary_key,
            getattr(keep, "id", None),
        )

        # Log initial work counts for both authors to help debug merge behaviour.
        self._log_work_counts(context, keep, merge)

        # Execute each merge command
        for command in self.commands:
            command.execute(context, keep, merge)

        # Safety check: after all merge commands, ensure there are no remaining
        # AuthorWork rows that still reference the merged author. If any remain,
        # delete them explicitly to avoid NOT NULL constraint failures when the
        # merged AuthorMetadata row is deleted.
        self._cleanup_remaining_works(context, merge)

        if keep.id is not None:
            final_keep_works = context.session.exec(
                select(AuthorWork).where(AuthorWork.author_metadata_id == keep.id)
            ).all()
            logger.debug(
                "AuthorMerger.merge: after commands, keep.id=%s has %d works (ids=%s)",
                keep.id,
                len(final_keep_works),
                [w.id for w in final_keep_works],
            )

        # Finally, delete the merged record now that all related rows have been
        # re-pointed or removed.
        context.session.delete(merge)
        context.session.flush()

    def merge_pair(
        self,
        context: "PipelineContext",
        pair: "DuplicatePair",
    ) -> None:
        """Merge a single duplicate pair.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        pair : DuplicatePair
            Duplicate pair to merge.
        """
        # Cache names and keys before merge to avoid accessing expired objects after rollback
        keep_name = pair.keep.name
        keep_key = pair.keep.openlibrary_key
        merge_name = pair.merge.name
        merge_key = pair.merge.openlibrary_key

        logger.info(
            "Found duplicate: '%s' (%s, score: %.2f) and '%s' (%s, score: %.2f)",
            keep_name,
            keep_key,
            pair.keep_score,
            merge_name,
            merge_key,
            pair.merge_score,
        )

        try:
            self.merge(context, pair.keep, pair.merge)
        except IntegrityError as e:
            # Handle constraint violations - rollback and log
            logger.warning(
                "Failed to merge authors '%s' (%s) and '%s' (%s): %s",
                keep_name,
                keep_key,
                merge_name,
                merge_key,
                e,
            )
            context.session.rollback()
            raise
        except Exception:
            # Handle other errors - rollback and re-raise
            logger.exception(
                "Unexpected error merging authors '%s' (%s) and '%s' (%s)",
                keep_name,
                keep_key,
                merge_name,
                merge_key,
            )
            context.session.rollback()
            raise

    def merge_batch(
        self,
        context: "PipelineContext",
        pairs: list["DuplicatePair"],
    ) -> "MergeStats":
        """Merge a batch of duplicate pairs.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with database session.
        pairs : list[DuplicatePair]
            List of duplicate pairs to merge.

        Returns
        -------
        MergeStats
            Statistics about the merge operation.
        """
        stats = MergeStats(duplicates_found=len(pairs))

        for pair in pairs:
            try:
                self.merge_pair(context, pair)
                stats.merged += 1
            except Exception:
                logger.exception("Failed to merge pair")
                stats.failed += 1

        return stats


@dataclass
class MergeStats:
    """Statistics for merge operations.

    Attributes
    ----------
    merged : int
        Number of successful merges.
    failed : int
        Number of failed merges.
    duplicates_found : int
        Number of duplicate pairs found.
    total_checked : int
        Total number of pairs checked.
    """

    merged: int = 0
    failed: int = 0
    duplicates_found: int = 0
    total_checked: int = 0

    def to_dict(self) -> dict[str, int | float]:
        """Convert stats to dictionary.

        Returns
        -------
        dict[str, int | float]
            Statistics dictionary.
        """
        return {
            "merged": self.merged,
            "failed": self.failed,
            "duplicates_found": self.duplicates_found,
            "total_checked": self.total_checked,
        }
