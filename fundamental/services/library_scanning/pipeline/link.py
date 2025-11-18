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

"""Link stage for creating library-aware work-author linkages."""

import logging
from datetime import UTC, datetime

from sqlmodel import select

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class LinkStage(PipelineStage):
    """Stage that creates library-aware linkages between works and authors.

    Links books to AuthorMetadata via AuthorMapping + library context.
    Tracks which library each work belongs to.
    """

    def __init__(self) -> None:
        """Initialize link stage."""
        self._progress = 0.0

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "link"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the link stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with match results and crawled data.

        Returns
        -------
        StageResult
            Result with linked mappings count.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Link cancelled")

        try:
            # Create mappings from match results
            # Each match result has the calibre_author_id stored
            author_id_to_metadata: dict[int, int] = {}
            total_matches = len(context.match_results)

            for idx, match_result in enumerate(context.match_results):
                if context.check_cancelled():
                    return StageResult(success=False, message="Link cancelled")

                if match_result.calibre_author_id is None:
                    continue

                # Get AuthorMetadata for this match
                stmt = select(AuthorMetadata).where(
                    AuthorMetadata.openlibrary_key == match_result.matched_entity.key,
                )
                author_metadata = context.session.exec(stmt).first()

                if author_metadata:
                    author_id_to_metadata[match_result.calibre_author_id] = (
                        author_metadata.id
                    )

                    # Create or update AuthorMapping
                    mapping_stmt = select(AuthorMapping).where(
                        AuthorMapping.calibre_author_id
                        == match_result.calibre_author_id,
                    )
                    existing_mapping = context.session.exec(mapping_stmt).first()

                    if existing_mapping:
                        # Update existing mapping
                        existing_mapping.author_metadata_id = author_metadata.id
                        existing_mapping.confidence_score = (
                            match_result.confidence_score
                        )
                        existing_mapping.matched_by = match_result.match_method
                        existing_mapping.updated_at = datetime.now(UTC)
                    else:
                        # Create new mapping
                        mapping = AuthorMapping(
                            calibre_author_id=match_result.calibre_author_id,
                            author_metadata_id=author_metadata.id,
                            confidence_score=match_result.confidence_score,
                            matched_by=match_result.match_method,
                        )
                        context.session.add(mapping)

                # Update progress
                if total_matches > 0:
                    self._progress = (idx + 1) / total_matches
                    metadata = {
                        "current_index": idx + 1,
                        "total_items": total_matches,
                        "mappings_created": len(author_id_to_metadata),
                    }
                    context.update_progress(self._progress, metadata)

            # Commit mappings
            context.session.commit()

            stats = {
                "mappings_created": len(author_id_to_metadata),
                "total_authors": len(context.crawled_authors),
            }

            logger.info(
                "Created %d author mappings for library %d",
                len(author_id_to_metadata),
                context.library_id,
            )

            return StageResult(
                success=True,
                message=f"Created {len(author_id_to_metadata)} author mappings",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in link stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Link failed: {e}",
            )
