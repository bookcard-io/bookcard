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

"""Scoring strategies for ranking search results.

Implements strategy pattern for extensible scoring algorithms.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime

from bookcard.models.pvr import IndexerDefinition
from bookcard.pvr.models import ReleaseInfo
from bookcard.services.pvr.search.utils import ensure_utc, normalize_text


@dataclass(frozen=True)
class ScoringWeights:
    """Configuration for release scoring weights.

    Attributes
    ----------
    TITLE_MATCH_FULL : float
        Score for full title match.
    TITLE_MATCH_PARTIAL : float
        Score for partial title match.
    AUTHOR_MATCH_FULL : float
        Score for full author match.
    AUTHOR_MATCH_PARTIAL : float
        Score for partial author match.
    ISBN_MATCH : float
        Score for ISBN match.
    FORMAT_QUALITY : float
        Score for preferred format.
    SEEDER_MAX : float
        Maximum score for seeder count.
    RECENCY_WEEK : float
        Score for releases within a week.
    RECENCY_MONTH : float
        Score for releases within a month.
    RECENCY_QUARTER : float
        Score for releases within a quarter.
    INDEXER_PRIORITY_MAX : float
        Maximum score for indexer priority bonus.
    """

    TITLE_MATCH_FULL: float = 0.4
    TITLE_MATCH_PARTIAL: float = 0.2
    AUTHOR_MATCH_FULL: float = 0.3
    AUTHOR_MATCH_PARTIAL: float = 0.15
    ISBN_MATCH: float = 0.2
    FORMAT_QUALITY: float = 0.1
    SEEDER_MAX: float = 0.1
    RECENCY_WEEK: float = 0.05
    RECENCY_MONTH: float = 0.03
    RECENCY_QUARTER: float = 0.01
    INDEXER_PRIORITY_MAX: float = 0.05


class ScoringStrategy(ABC):
    """Abstract base class for scoring strategies.

    Follows strategy pattern to allow extensible scoring algorithms.
    """

    @abstractmethod
    def score(
        self,
        release: ReleaseInfo,
        query: str,
        title: str | None,
        author: str | None,
        isbn: str | None,
        indexer: IndexerDefinition,
    ) -> float:
        """Calculate relevance score for a release.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.
        query : str
            Original search query.
        title : str | None
            Original title query.
        author : str | None
            Original author query.
        isbn : str | None
            Original ISBN query.
        indexer : IndexerDefinition
            Indexer that provided this release.

        Returns
        -------
        float
            Score between 0.0 and 1.0 (higher is better).
        """
        raise NotImplementedError


class DefaultScoringStrategy(ScoringStrategy):
    """Default scoring strategy implementation.

    Scores releases based on title/author/ISBN matches, format quality,
    seeder count, recency, and indexer priority.
    """

    def __init__(self, weights: ScoringWeights | None = None) -> None:
        """Initialize default scoring strategy.

        Parameters
        ----------
        weights : ScoringWeights | None
            Scoring weights configuration. If None, uses default weights.
        """
        self.weights = weights or ScoringWeights()

    def score(
        self,
        release: ReleaseInfo,
        query: str,  # noqa: ARG002
        title: str | None,
        author: str | None,
        isbn: str | None,
        indexer: IndexerDefinition,
    ) -> float:
        """Calculate relevance score for a release.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.
        query : str
            Original search query.
        title : str | None
            Original title query.
        author : str | None
            Original author query.
        isbn : str | None
            Original ISBN query.
        indexer : IndexerDefinition
            Indexer that provided this release.

        Returns
        -------
        float
            Score between 0.0 and 1.0 (higher is better).
        """
        score = 0.0
        score += self._score_title_match(title, release)
        score += self._score_author_match(author, release)
        score += self._score_isbn_match(isbn, release)
        score += self._score_format_quality(release)
        score += self._score_seeders(release)
        score += self._score_recency(release)
        score += self._score_indexer_priority(indexer)
        return min(1.0, max(0.0, score))

    def _score_title_match(self, title: str | None, release: ReleaseInfo) -> float:
        """Score title match.

        Parameters
        ----------
        title : str | None
            Title query.
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            Title match score.
        """
        if not title:
            return 0.0
        title_norm = normalize_text(title)
        release_title_norm = normalize_text(release.title)
        if title_norm in release_title_norm or release_title_norm in title_norm:
            return self.weights.TITLE_MATCH_FULL
        if any(word in release_title_norm for word in title_norm.split() if word):
            return self.weights.TITLE_MATCH_PARTIAL
        return 0.0

    def _score_author_match(self, author: str | None, release: ReleaseInfo) -> float:
        """Score author match.

        Parameters
        ----------
        author : str | None
            Author query.
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            Author match score.
        """
        if not author or not release.author:
            return 0.0
        author_norm = normalize_text(author)
        release_author_norm = normalize_text(release.author)
        if author_norm in release_author_norm or release_author_norm in author_norm:
            return self.weights.AUTHOR_MATCH_FULL
        if any(word in release_author_norm for word in author_norm.split() if word):
            return self.weights.AUTHOR_MATCH_PARTIAL
        return 0.0

    def _score_isbn_match(self, isbn: str | None, release: ReleaseInfo) -> float:
        """Score ISBN match.

        Parameters
        ----------
        isbn : str | None
            ISBN query.
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            ISBN match score.
        """
        if not isbn or not release.isbn:
            return 0.0
        isbn_normalized = isbn.replace("-", "").replace(" ", "")
        release_isbn_normalized = release.isbn.replace("-", "").replace(" ", "")
        if isbn_normalized == release_isbn_normalized:
            return self.weights.ISBN_MATCH
        return 0.0

    def _score_format_quality(self, release: ReleaseInfo) -> float:
        """Score format/quality.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            Format quality score.
        """
        if not release.quality:
            return 0.0
        quality_lower = release.quality.lower()
        if any(fmt in quality_lower for fmt in ["epub", "pdf", "mobi", "azw"]):
            return self.weights.FORMAT_QUALITY
        return 0.0

    def _score_seeders(self, release: ReleaseInfo) -> float:
        """Score seeder count.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            Seeder score.
        """
        if release.seeders is None:
            return 0.0
        return min(self.weights.SEEDER_MAX, release.seeders / 1000.0)

    def _score_recency(self, release: ReleaseInfo) -> float:
        """Score recency.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.

        Returns
        -------
        float
            Recency score.
        """
        if release.publish_date is None:
            return 0.0
        publish_date = ensure_utc(release.publish_date)
        if not publish_date:
            return 0.0
        age_days = (datetime.now(UTC) - publish_date).days
        if age_days <= 7:
            return self.weights.RECENCY_WEEK
        if age_days <= 30:
            return self.weights.RECENCY_MONTH
        if age_days <= 90:
            return self.weights.RECENCY_QUARTER
        return 0.0

    def _score_indexer_priority(self, indexer: IndexerDefinition) -> float:
        """Score indexer priority bonus.

        Parameters
        ----------
        indexer : IndexerDefinition
            Indexer definition.

        Returns
        -------
        float
            Priority bonus score.
        """
        return max(0.0, self.weights.INDEXER_PRIORITY_MAX - (indexer.priority / 1000.0))


class ReleaseScorer:
    """Component for scoring releases.

    Delegates to a scoring strategy, following SRP and DIP.
    """

    def __init__(self, strategy: ScoringStrategy) -> None:
        """Initialize release scorer.

        Parameters
        ----------
        strategy : ScoringStrategy
            Scoring strategy to use.
        """
        self.strategy = strategy

    def score_release(
        self,
        release: ReleaseInfo,
        query: str,
        title: str | None,
        author: str | None,
        isbn: str | None,
        indexer: IndexerDefinition,
    ) -> float:
        """Score a release using the configured strategy.

        Parameters
        ----------
        release : ReleaseInfo
            Release to score.
        query : str
            Original search query.
        title : str | None
            Original title query.
        author : str | None
            Original author query.
        isbn : str | None
            Original ISBN query.
        indexer : IndexerDefinition
            Indexer that provided this release.

        Returns
        -------
        float
            Score between 0.0 and 1.0.
        """
        return self.strategy.score(release, query, title, author, isbn, indexer)
