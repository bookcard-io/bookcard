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

"""Download decision service for evaluating releases.

Similar to Sonarr's decision engine, evaluates releases against user preferences
and returns download decisions with approval status and rejection reasons.
"""

import logging
from collections.abc import Sequence

from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.decision.models import DownloadDecision
from bookcard.services.pvr.decision.preferences import DownloadDecisionPreferences
from bookcard.services.pvr.decision.specifications import (
    AgeSpecification,
    AuthorMatchSpecification,
    BlocklistSpecification,
    FormatSpecification,
    IDownloadDecisionSpecification,
    IndexerSpecification,
    ISBNMatchSpecification,
    KeywordSpecification,
    MetadataSpecification,
    SeederSpecification,
    SizeSpecification,
    TitleMatchSpecification,
)

logger = logging.getLogger(__name__)


class DownloadDecisionService:
    """Service for evaluating releases and making download decisions.

    Uses specification pattern to check various criteria and determine
    if a release should be downloaded.

    Parameters
    ----------
    specifications : Sequence[IDownloadDecisionSpecification] | None
        Custom specifications to use. If None, uses default set.
    """

    def __init__(
        self,
        specifications: Sequence[IDownloadDecisionSpecification] | None = None,
    ) -> None:
        """Initialize download decision service.

        Parameters
        ----------
        specifications : Sequence[IDownloadDecisionSpecification] | None
            Custom specifications. If None, uses default set.
        """
        self._specifications = list(specifications) if specifications else []

    def evaluate_release(
        self,
        release: ReleaseInfo,
        preferences: DownloadDecisionPreferences,
        search_title: str | None = None,
        search_author: str | None = None,
        search_isbn: str | None = None,
        score: float = 0.0,
    ) -> DownloadDecision:
        """Evaluate a release and make a download decision.

        Checks the release against all specifications and user preferences,
        returning a decision with approval status and any rejection reasons.

        Parameters
        ----------
        release : ReleaseInfo
            Release to evaluate.
        preferences : DownloadDecisionPreferences
            User preferences and criteria.
        search_title : str | None
            Expected title from search (for matching).
        search_author : str | None
            Expected author from search (for matching).
        search_isbn : str | None
            Expected ISBN from search (for matching).
        score : float
            Quality/relevance score (0.0-1.0) from scoring service.

        Returns
        -------
        DownloadDecision
            Decision result with approval status and rejections.
        """
        decision = DownloadDecision(release=release, score=score)

        # Get specifications to check
        specs = self._get_specifications(
            search_title=search_title,
            search_author=search_author,
            search_isbn=search_isbn,
        )

        # Check each specification
        for spec in specs:
            is_satisfied, rejection = spec.is_satisfied_by(release, preferences)
            if not is_satisfied and rejection is not None:
                decision.add_rejection(
                    reason=rejection.reason,
                    message=rejection.message,
                    rejection_type=rejection.type,
                )

        if decision.approved:
            logger.debug(
                "Release '%s' approved for download (score: %.2f)",
                release.title,
                score,
            )
        else:
            rejection_messages = [r.message for r in decision.rejections]
            logger.debug(
                "Release '%s' rejected: %s",
                release.title,
                "; ".join(rejection_messages),
            )

        return decision

    def _get_specifications(
        self,
        search_title: str | None = None,
        search_author: str | None = None,
        search_isbn: str | None = None,
    ) -> list[IDownloadDecisionSpecification]:
        """Get list of specifications to check.

        Parameters
        ----------
        search_title : str | None
            Expected title.
        search_author : str | None
            Expected author.
        search_isbn : str | None
            Expected ISBN.

        Returns
        -------
        list[IDownloadDecisionSpecification]
            List of specifications to check.
        """
        if self._specifications:
            return self._specifications

        # Default specifications in order of checking
        specs: list[IDownloadDecisionSpecification] = [
            MetadataSpecification(),  # Check basic requirements first
            BlocklistSpecification(),  # Check blocklist early
            IndexerSpecification(),  # Check indexer restrictions
            FormatSpecification(),  # Check format preferences
            SizeSpecification(),  # Check size constraints
            SeederSpecification(),  # Check seeder requirements
            AgeSpecification(),  # Check age constraints
            KeywordSpecification(),  # Check keyword requirements
        ]

        # Add match specifications if search criteria provided
        if search_title is not None:
            specs.append(TitleMatchSpecification(search_title))
        if search_author is not None:
            specs.append(AuthorMatchSpecification(search_author))
        if search_isbn is not None:
            specs.append(ISBNMatchSpecification(search_isbn))

        return specs

    def evaluate_releases(
        self,
        releases: list[ReleaseInfo],
        preferences: DownloadDecisionPreferences,
        search_title: str | None = None,
        search_author: str | None = None,
        search_isbn: str | None = None,
        scores: dict[str, float] | None = None,
    ) -> list[DownloadDecision]:
        """Evaluate multiple releases and make download decisions.

        Parameters
        ----------
        releases : list[ReleaseInfo]
            Releases to evaluate.
        preferences : DownloadDecisionPreferences
            User preferences and criteria.
        search_title : str | None
            Expected title from search.
        search_author : str | None
            Expected author from search.
        search_isbn : str | None
            Expected ISBN from search.
        scores : dict[str, float] | None
            Optional scores keyed by release download_url.

        Returns
        -------
        list[DownloadDecision]
            List of decisions, one per release.
        """
        decisions: list[DownloadDecision] = []
        scores_dict = scores or {}

        for release in releases:
            score = scores_dict.get(release.download_url, 0.0)
            decision = self.evaluate_release(
                release=release,
                preferences=preferences,
                search_title=search_title,
                search_author=search_author,
                search_isbn=search_isbn,
                score=score,
            )
            decisions.append(decision)

        return decisions
