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

"""Match stage for matching crawled entities to external data sources."""

import logging

from fundamental.services.library_scanning.matching.orchestrator import (
    MatchingOrchestrator,
)
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class MatchStage(PipelineStage):
    """Stage that matches crawled entities to external data sources.

    Uses MatchingOrchestrator with configured strategies to match authors.
    Creates AuthorMapping records with confidence scores.
    """

    def __init__(self, min_confidence: float = 0.5) -> None:
        """Initialize match stage.

        Parameters
        ----------
        min_confidence : float
            Minimum confidence score to accept a match (default: 0.5).
        """
        self._progress = 0.0
        self._min_confidence = min_confidence
        self._matching_orchestrator = MatchingOrchestrator(
            min_confidence=min_confidence,
        )

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "match"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the match stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with crawled authors and data source.

        Returns
        -------
        StageResult
            Result with match results and unmatched authors.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Match cancelled")

        try:
            authors = context.crawled_authors
            total_authors = len(authors)

            if total_authors == 0:
                return StageResult(
                    success=True,
                    message="No authors to match",
                    stats={"matched": 0, "unmatched": 0},
                )

            matched_count = 0
            unmatched_count = 0

            for idx, author in enumerate(authors):
                if context.check_cancelled():
                    return StageResult(success=False, message="Match cancelled")

                # Attempt to match author
                match_result = self._matching_orchestrator.match(
                    author,
                    context.data_source,
                )

                if match_result:
                    # Store the Calibre author ID for tracking
                    match_result.calibre_author_id = author.id
                    context.match_results.append(match_result)
                    matched_count += 1
                else:
                    context.unmatched_authors.append(author)
                    unmatched_count += 1

                # Update progress with metadata
                self._progress = (idx + 1) / total_authors
                metadata = {
                    "current_item": author.name,
                    "current_index": idx + 1,
                    "total_items": total_authors,
                    "matched": matched_count,
                    "unmatched": unmatched_count,
                }
                context.update_progress(self._progress, metadata)

            stats = {
                "matched": matched_count,
                "unmatched": unmatched_count,
                "total": total_authors,
            }

            logger.info(
                "Matched %d/%d authors in library %d",
                matched_count,
                total_authors,
                context.library_id,
            )

            return StageResult(
                success=True,
                message=f"Matched {matched_count}/{total_authors} authors",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in match stage")
            return StageResult(
                success=False,
                message=f"Match failed: {e}",
            )
