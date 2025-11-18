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

"""Base pipeline stage abstraction."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from fundamental.services.library_scanning.pipeline.context import PipelineContext


@dataclass
class StageResult:
    """Result of executing a pipeline stage.

    Attributes
    ----------
    success : bool
        Whether the stage completed successfully.
    message : str | None
        Optional message describing the result.
    stats : dict[str, int | float] | None
        Optional statistics about the stage execution.
    """

    success: bool
    message: str | None = None
    stats: dict[str, int | float] | None = None


class PipelineStage(ABC):
    """Abstract base class for pipeline stages.

    Pipeline stages execute sequentially to crawl, match, ingest,
    link, and score library data. Each stage reports progress and
    can be cancelled.
    """

    @abstractmethod
    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the pipeline stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with library, session, data source, etc.

        Returns
        -------
        StageResult
            Result of stage execution.

        Raises
        ------
        Exception
            If stage execution fails critically.
        """
        raise NotImplementedError

    @abstractmethod
    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        raise NotImplementedError

    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name (e.g., "crawl", "match", "ingest").
        """
        raise NotImplementedError
