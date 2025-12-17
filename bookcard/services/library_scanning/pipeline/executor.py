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

"""Pipeline executor for orchestrating stage execution."""

import logging
from collections.abc import Callable, Sequence
from typing import Any

from bookcard.services.library_scanning.pipeline.base import PipelineStage
from bookcard.services.library_scanning.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """Orchestrates pipeline stage execution.

    Manages progress tracking (0.0-1.0 across all stages), handles errors,
    cancellation, and stage rollback. Reports progress via callback.
    """

    def __init__(
        self,
        stages: Sequence[PipelineStage],
        progress_callback: Callable[[float], None] | None = None,
    ) -> None:
        """Initialize pipeline executor.

        Parameters
        ----------
        stages : Sequence[PipelineStage]
            Pipeline stages to execute in order.
        progress_callback : callable[[float], None] | None
            Optional callback for reporting overall progress (0.0 to 1.0).
        """
        self.stages = list(stages)
        self.progress_callback = progress_callback
        self._current_stage_index = 0

    def execute(self, context: PipelineContext) -> dict[str, object]:
        """Execute all pipeline stages in sequence.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with library, session, data source, etc.

        Returns
        -------
        dict[str, object]
            Summary of execution with stage results and statistics.
        """
        total_stages = len(self.stages)
        stage_results: list[dict[str, object]] = []

        # Set progress callback in context
        if self.progress_callback:
            context.progress_callback = self._create_progress_callback(
                total_stages,
            )

        for idx, stage in enumerate(self.stages):
            if context.check_cancelled():
                logger.info("Pipeline execution cancelled at stage %s", stage.name)
                return {
                    "success": False,
                    "message": "Pipeline cancelled",
                    "stage_results": stage_results,
                    "completed_stages": idx,
                    "total_stages": total_stages,
                }

            logger.info(
                "Starting pipeline stage %d/%d: %s (library %d)",
                idx + 1,
                total_stages,
                stage.name,
                context.library_id,
            )

            try:
                # Execute stage
                result = stage.execute(context)

                stage_result = {
                    "stage": stage.name,
                    "success": result.success,
                    "message": result.message,
                    "stats": result.stats,
                }
                stage_results.append(stage_result)

                if not result.success:
                    logger.error(
                        "Pipeline stage %s failed: %s",
                        stage.name,
                        result.message,
                    )
                    # Continue to next stage (non-critical failure)
                    # In production, might want to make this configurable
                else:
                    logger.info(
                        "Pipeline stage %s completed successfully: %s",
                        stage.name,
                        result.message,
                    )

                # Update overall progress with stage metadata
                # Use nested structure to prevent stale metadata from previous stages
                stage_progress = (idx + 1) / total_stages
                if self.progress_callback:
                    stage_metadata = {
                        "current_stage": {
                            "name": stage.name,
                            "index": idx,
                            "total_stages": total_stages,
                            "status": "complete" if result.success else "failed",
                            "stats": result.stats,
                            "message": result.message,
                        },
                    }
                    self.progress_callback(stage_progress, stage_metadata)

                self._current_stage_index = idx + 1

            except Exception as e:
                logger.exception("Critical error in pipeline stage %s", stage.name)
                stage_result = {
                    "stage": stage.name,
                    "success": False,
                    "message": f"Critical error: {e}",
                    "stats": None,
                }
                stage_results.append(stage_result)

                # Decide whether to continue or abort
                # For now, we'll continue but mark as failed
                # In production, might want to make this configurable

        # Determine overall success
        all_successful = all(r["success"] for r in stage_results)

        return {
            "success": all_successful,
            "message": f"Pipeline completed: {sum(1 for r in stage_results if r['success'])}/{total_stages} stages successful",
            "stage_results": stage_results,
            "completed_stages": total_stages,
            "total_stages": total_stages,
        }

    def _create_progress_callback(
        self,
        total_stages: int,
    ) -> Callable[[float, dict[str, Any] | None], None]:
        """Create a progress callback that accounts for stage progress.

        Parameters
        ----------
        total_stages : int
            Total number of stages.

        Returns
        -------
        callable[[float, dict[str, Any] | None], None]
            Progress callback function.
        """

        def callback(
            stage_progress: float,
            metadata: dict[str, Any] | None = None,
        ) -> None:
            """Update overall progress based on current stage progress.

            Parameters
            ----------
            stage_progress : float
                Progress within current stage (0.0 to 1.0).
            metadata : dict[str, Any] | None
                Optional metadata from the stage.
            """
            if self.progress_callback:
                # Calculate overall progress
                # Current stage contributes (1/total_stages) to overall progress
                stage_weight = 1.0 / total_stages
                completed_stages_progress = self._current_stage_index * stage_weight
                current_stage_progress = stage_progress * stage_weight
                overall_progress = completed_stages_progress + current_stage_progress

                self.progress_callback(overall_progress, metadata)

        return callback
