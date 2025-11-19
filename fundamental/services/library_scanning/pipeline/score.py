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

"""Score stage for calculating author similarity scores."""

import logging
import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlmodel import select

from fundamental.models.author_metadata import (
    AuthorMetadata,
    AuthorSimilarity,
    AuthorWork,
    WorkSubject,
)
from fundamental.services.library_scanning.pipeline.base import (
    PipelineStage,
    StageResult,
)
from fundamental.services.library_scanning.pipeline.context import PipelineContext

if TYPE_CHECKING:
    from sqlmodel import Session

logger = logging.getLogger(__name__)


# ============================================================================
# Utility Classes
# ============================================================================


class DateParser:
    """Utility class for parsing date strings."""

    @staticmethod
    def extract_year(date_str: str) -> int | None:
        """Extract year from a date string.

        Parameters
        ----------
        date_str : str
            Date string (e.g., "31 July 1965" or "1965").

        Returns
        -------
        int | None
            Extracted year, or None if not found.
        """
        match = re.search(r"\b(19|20)\d{2}\b", date_str)
        return int(match.group()) if match else None


class SimilarityMetrics:
    """Utility class for similarity calculation metrics."""

    @staticmethod
    def normalize_ratio(value1: float, value2: float) -> float:
        """Calculate normalized ratio for similarity.

        Parameters
        ----------
        value1 : float
            First value.
        value2 : float
            Second value.

        Returns
        -------
        float
            Normalized ratio between 0.0 and 1.0, or 0.0 if either value is 0.
        """
        if value1 == 0 or value2 == 0:
            return 0.0
        return min(value1, value2) / max(value1, value2)

    @staticmethod
    def jaccard(set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity between two sets.

        Parameters
        ----------
        set1 : set[str]
            First set.
        set2 : set[str]
            Second set.

        Returns
        -------
        float
            Jaccard similarity between 0.0 and 1.0.
        """
        if not set1 or not set2:
            return 0.0
        intersection = set1 & set2
        union = set1 | set2
        return len(intersection) / len(union) if union else 0.0


# ============================================================================
# Repository Classes
# ============================================================================


class AuthorRepository:
    """Repository for author metadata access."""

    def __init__(self, session: "Session") -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def get_all(self, limit: int | None = None) -> list[AuthorMetadata]:
        """Get all author metadata records.

        Parameters
        ----------
        limit : int | None
            Maximum number of authors to return (None = no limit).

        Returns
        -------
        list[AuthorMetadata]
            List of author metadata records.
        """
        stmt = select(AuthorMetadata)
        authors = list(self.session.exec(stmt).all())
        return authors[:limit] if limit else authors

    def get_by_id(self, author_id: int) -> AuthorMetadata | None:
        """Get author by ID.

        Parameters
        ----------
        author_id : int
            Author ID.

        Returns
        -------
        AuthorMetadata | None
            Author metadata if found, None otherwise.
        """
        return self.session.get(AuthorMetadata, author_id)


class SubjectRepository:
    """Repository for subject/genre access."""

    def __init__(self, session: "Session") -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def get_subjects_for_author(self, author_id: int) -> set[str]:
        """Get all subjects for an author from their works.

        Parameters
        ----------
        author_id : int
            Author ID.

        Returns
        -------
        set[str]
            Set of subject names.
        """
        stmt = (
            select(WorkSubject)
            .join(AuthorWork, WorkSubject.author_work_id == AuthorWork.id)
            .where(AuthorWork.author_metadata_id == author_id)
        )
        subjects = self.session.exec(stmt).all()
        return {s.subject_name for s in subjects}


class SimilarityRepository:
    """Repository for author similarity access."""

    def __init__(self, session: "Session") -> None:
        """Initialize repository.

        Parameters
        ----------
        session : Session
            Database session.
        """
        self.session = session

    def exists(self, author1_id: int, author2_id: int) -> bool:
        """Check if similarity record exists between two authors.

        Parameters
        ----------
        author1_id : int
            First author ID.
        author2_id : int
            Second author ID.

        Returns
        -------
        bool
            True if similarity exists, False otherwise.
        """
        stmt = select(AuthorSimilarity).where(
            (
                (AuthorSimilarity.author1_id == author1_id)
                & (AuthorSimilarity.author2_id == author2_id)
            )
            | (
                (AuthorSimilarity.author1_id == author2_id)
                & (AuthorSimilarity.author2_id == author1_id)
            ),
        )
        return self.session.exec(stmt).first() is not None

    def has_fresh_similarities(
        self, author_id: int, stale_data_max_age_days: int
    ) -> bool:
        """Check if author has any fresh similarity records.

        Parameters
        ----------
        author_id : int
            Author ID to check.
        stale_data_max_age_days : int
            Maximum age in days for similarities to be considered fresh.

        Returns
        -------
        bool
            True if author has at least one similarity record within the stale age,
            False otherwise.
        """
        now = datetime.now(UTC)
        cutoff_date = now - timedelta(days=stale_data_max_age_days)

        stmt = select(AuthorSimilarity).where(
            (
                (AuthorSimilarity.author1_id == author_id)
                | (AuthorSimilarity.author2_id == author_id)
            )
            & (AuthorSimilarity.created_at >= cutoff_date)
        )
        return self.session.exec(stmt).first() is not None

    def create(
        self,
        author1_id: int,
        author2_id: int,
        score: float,
        source: str = "composite",
    ) -> AuthorSimilarity:
        """Create a similarity record.

        Ensures consistent ordering (lower ID first).

        Parameters
        ----------
        author1_id : int
            First author ID.
        author2_id : int
            Second author ID.
        score : float
            Similarity score (0.0 to 1.0).
        source : str
            Similarity source identifier.

        Returns
        -------
        AuthorSimilarity
            Created similarity record.
        """
        # Ensure consistent ordering (lower ID first)
        if author1_id > author2_id:
            author1_id, author2_id = author2_id, author1_id

        similarity = AuthorSimilarity(
            author1_id=author1_id,
            author2_id=author2_id,
            similarity_score=score,
            similarity_source=source,
        )
        self.session.add(similarity)
        return similarity


# ============================================================================
# Similarity Calculator Classes
# ============================================================================


class SimilarityCalculator(ABC):
    """Abstract base class for similarity calculators."""

    @abstractmethod
    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate similarity between two authors.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        raise NotImplementedError


class GenreSimilarityCalculator(SimilarityCalculator):
    """Calculator for genre/subject-based similarity."""

    def __init__(self, subject_repository: SubjectRepository) -> None:
        """Initialize calculator.

        Parameters
        ----------
        subject_repository : SubjectRepository
            Repository for accessing subjects.
        """
        self.subject_repository = subject_repository

    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate similarity based on genre/subject overlap.

        Uses Jaccard similarity with a boost for shared subjects.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if author1.id is None or author2.id is None:
            return 0.0

        subjects1 = self.subject_repository.get_subjects_for_author(author1.id)
        subjects2 = self.subject_repository.get_subjects_for_author(author2.id)

        if not subjects1 or not subjects2:
            return 0.0

        # Calculate base Jaccard similarity
        genre_similarity = SimilarityMetrics.jaccard(subjects1, subjects2)

        # Boost similarity if they share subjects
        shared_subjects_count = len(subjects1 & subjects2)
        if shared_subjects_count > 0:
            # Add boost based on number of shared subjects
            # 1-2 shared: +0.05, 3-5: +0.10, 6+: +0.15
            if shared_subjects_count <= 2:
                boost = 0.05
            elif shared_subjects_count <= 5:
                boost = 0.10
            else:
                boost = 0.15
            genre_similarity = min(1.0, genre_similarity + boost)

        return genre_similarity


class WorkCountSimilarityCalculator(SimilarityCalculator):
    """Calculator for work count-based similarity."""

    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate similarity based on work count.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if (
            author1.work_count is None
            or author2.work_count is None
            or author1.work_count == 0
            or author2.work_count == 0
        ):
            return 0.0

        return SimilarityMetrics.normalize_ratio(
            float(author1.work_count), float(author2.work_count)
        )


class RatingsSimilarityCalculator(SimilarityCalculator):
    """Calculator for ratings count-based similarity."""

    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate similarity based on ratings count.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if (
            author1.ratings_count is None
            or author2.ratings_count is None
            or author1.ratings_count == 0
            or author2.ratings_count == 0
        ):
            return 0.0

        return SimilarityMetrics.normalize_ratio(
            float(author1.ratings_count), float(author2.ratings_count)
        )


class TimePeriodSimilarityCalculator(SimilarityCalculator):
    """Calculator for time period-based similarity."""

    def __init__(self, max_year_diff: int = 50) -> None:
        """Initialize calculator.

        Parameters
        ----------
        max_year_diff : int
            Maximum year difference for similarity (default: 50).
        """
        self.max_year_diff = max_year_diff

    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate similarity based on birth year proximity.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Similarity score between 0.0 and 1.0.
        """
        if not author1.birth_date or not author2.birth_date:
            return 0.0

        year1 = DateParser.extract_year(author1.birth_date)
        year2 = DateParser.extract_year(author2.birth_date)

        if year1 is None or year2 is None:
            return 0.0

        year_diff = abs(year1 - year2)
        if year_diff > self.max_year_diff:
            return 0.0

        return 1.0 - (year_diff / self.max_year_diff)


class CompositeSimilarityCalculator(SimilarityCalculator):
    """Composite calculator that combines multiple similarity metrics."""

    def __init__(
        self,
        calculators: list[tuple[SimilarityCalculator, float]],
    ) -> None:
        """Initialize composite calculator.

        Parameters
        ----------
        calculators : list[tuple[SimilarityCalculator, float]]
            List of (calculator, weight) tuples.
        """
        self.calculators = calculators

    def calculate(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> float:
        """Calculate weighted composite similarity.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        float
            Weighted similarity score between 0.0 and 1.0.
        """
        factors: list[float] = []
        weights: list[float] = []

        # Collect all non-zero similarity factors
        for calculator, weight in self.calculators:
            similarity = calculator.calculate(author1, author2)
            if similarity > 0:
                factors.append(similarity)
                weights.append(weight)

        if not factors:
            # Very low similarity when we have no data to compare
            return 0.05

        # Normalize weights to sum to 1.0
        total_weight = sum(weights)
        if total_weight > 0:
            normalized_weights = [w / total_weight for w in weights]
            weighted_similarity = sum(
                f * w for f, w in zip(factors, normalized_weights, strict=True)
            )
            return min(1.0, weighted_similarity)

        # Fallback: simple average if weights don't work
        return min(1.0, sum(factors) / len(factors))


# ============================================================================
# Progress Tracking and Processing Classes
# ============================================================================


class ProgressTracker:
    """Tracks progress for batch processing operations."""

    def __init__(self, total_items: int, log_interval: int = 100) -> None:
        """Initialize progress tracker.

        Parameters
        ----------
        total_items : int
            Total number of items to process.
        log_interval : int
            Number of items between progress logs (default: 100).
        """
        self.total_items = total_items
        self.processed_items = 0
        self.log_interval = log_interval
        self._progress = 0.0

    def update(self, items_processed: int = 1) -> float:
        """Update progress.

        Parameters
        ----------
        items_processed : int
            Number of items processed in this update (default: 1).

        Returns
        -------
        float
            Current progress value between 0.0 and 1.0.
        """
        self.processed_items += items_processed
        self._progress = (
            self.processed_items / self.total_items if self.total_items > 0 else 0.0
        )
        return self._progress

    def should_log(self) -> bool:
        """Check if progress should be logged.

        Returns
        -------
        bool
            True if progress should be logged, False otherwise.
        """
        return (
            self.processed_items % self.log_interval == 0
            or self.processed_items == self.total_items
        )

    @property
    def progress(self) -> float:
        """Get current progress.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        return self._progress


class AuthorPairProcessor:
    """Processes author pairs and creates similarity records."""

    def __init__(
        self,
        similarity_calculator: SimilarityCalculator,
        similarity_repository: SimilarityRepository,
        min_similarity: float = 0.5,
    ) -> None:
        """Initialize processor.

        Parameters
        ----------
        similarity_calculator : SimilarityCalculator
            Calculator for similarity scores.
        similarity_repository : SimilarityRepository
            Repository for similarity records.
        min_similarity : float
            Minimum similarity score to create a record (default: 0.5).
        """
        self.calculator = similarity_calculator
        self.repository = similarity_repository
        self.min_similarity = min_similarity

    def process_pair(
        self,
        author1: AuthorMetadata,
        author2: AuthorMetadata,
    ) -> bool:
        """Process a single author pair.

        Parameters
        ----------
        author1 : AuthorMetadata
            First author.
        author2 : AuthorMetadata
            Second author.

        Returns
        -------
        bool
            True if similarity was created, False otherwise.
        """
        # Skip if same author
        if author1.id == author2.id:
            return False

        # Skip if similarity already exists
        if (
            author1.id is not None
            and author2.id is not None
            and self.repository.exists(author1.id, author2.id)
        ):
            return False

        # Calculate similarity
        score = self.calculator.calculate(author1, author2)

        # Create similarity if above threshold
        if (
            score >= self.min_similarity
            and author1.id is not None
            and author2.id is not None
        ):
            self.repository.create(author1.id, author2.id, score, "composite")
            return True

        return False


# ============================================================================
# Score Stage
# ============================================================================


class ScoreStage(PipelineStage):
    """Stage that calculates similarity scores between authors.

    Uses ONLY persisted data from the database (no API calls).
    Creates AuthorSimilarity records using genre overlap, collaboration
    detection, and work similarity based on persisted subjects and works.
    """

    def __init__(
        self,
        min_similarity: float = 0.5,
        author_limit: int | None = None,
        author_repository: AuthorRepository | None = None,
        similarity_repository: SimilarityRepository | None = None,
        subject_repository: SubjectRepository | None = None,
        similarity_calculator: SimilarityCalculator | None = None,
        stale_data_max_age_days: int | None = None,
    ) -> None:
        """Initialize score stage.

        Parameters
        ----------
        min_similarity : float
            Minimum similarity score to store (default: 0.5).
        author_limit : int | None
            Maximum number of authors to process (None = no limit).
            Used for testing to limit processing.
        author_repository : AuthorRepository | None
            Repository for author access (created from context if None).
        similarity_repository : SimilarityRepository | None
            Repository for similarity access (created from context if None).
        subject_repository : SubjectRepository | None
            Repository for subject access (created from context if None).
        similarity_calculator : SimilarityCalculator | None
            Calculator for similarity scores (default composite created if None).
        stale_data_max_age_days : int | None
            Maximum age in days for existing similarities to be considered fresh.
            If an author has similarities within this age, re-analysis will be skipped.
            None means always analyze (no staleness check).
        """
        self._progress = 0.0
        self._min_similarity = min_similarity
        self._author_limit = author_limit
        self._author_repository = author_repository
        self._similarity_repository = similarity_repository
        self._subject_repository = subject_repository
        self._similarity_calculator = similarity_calculator
        self._stale_data_max_age_days = stale_data_max_age_days
        self._progress_tracker: ProgressTracker | None = None

    def _create_repositories(self, session: "Session") -> None:
        """Create repositories from session if not already set.

        Parameters
        ----------
        session : Session
            Database session.
        """
        if self._author_repository is None:
            self._author_repository = AuthorRepository(session)
        if self._similarity_repository is None:
            self._similarity_repository = SimilarityRepository(session)
        if self._subject_repository is None:
            self._subject_repository = SubjectRepository(session)

    def _ensure_author_repository_initialized(self) -> None:
        """Ensure author repository is initialized.

        Raises
        ------
        ValueError
            If author repository is not initialized.
        """
        if self._author_repository is None:
            msg = "Author repository must be initialized"
            raise ValueError(msg)

    def _raise_repository_not_initialized_error(self) -> None:
        """Raise error for uninitialized repository.

        Raises
        ------
        RuntimeError
            Always raised to indicate repository is not initialized.
        """
        msg = "Author repository must be initialized"
        raise RuntimeError(msg)

    def _raise_missing_get_all_method_error(self) -> None:
        """Raise error for missing get_all method.

        Raises
        ------
        AttributeError
            Always raised to indicate get_all method is missing.
        """
        msg = "Author repository must have get_all method"
        raise AttributeError(msg)

    def _create_default_calculator(self) -> SimilarityCalculator:
        """Create default composite similarity calculator.

        Returns
        -------
        SimilarityCalculator
            Composite calculator with default weights.
        """
        if self._subject_repository is None:
            msg = "Subject repository must be initialized first"
            raise ValueError(msg)

        return CompositeSimilarityCalculator([
            (GenreSimilarityCalculator(self._subject_repository), 0.5),
            (WorkCountSimilarityCalculator(), 0.2),
            (RatingsSimilarityCalculator(), 0.15),
            (TimePeriodSimilarityCalculator(), 0.15),
        ])

    @property
    def name(self) -> str:
        """Get the name of this pipeline stage.

        Returns
        -------
        str
            Stage name.
        """
        return "score"

    def get_progress(self) -> float:
        """Get current progress of this stage.

        Returns
        -------
        float
            Progress value between 0.0 and 1.0.
        """
        if self._progress_tracker is not None:
            return self._progress_tracker.progress
        return self._progress

    def _should_skip_author(self, author: AuthorMetadata) -> bool:
        """Check if author should be skipped due to existing fresh similarities.

        Parameters
        ----------
        author : AuthorMetadata
            Author to check.

        Returns
        -------
        bool
            True if author should be skipped, False otherwise.
        """
        # If no stale data settings, never skip
        if self._stale_data_max_age_days is None:
            return False

        # Skip if author has no ID
        if author.id is None:
            return False

        # Check if author has fresh similarities
        if self._similarity_repository is None:
            return False

        return self._similarity_repository.has_fresh_similarities(
            author.id, self._stale_data_max_age_days
        )

    def _filter_authors_by_staleness(
        self,
        all_authors: list[AuthorMetadata],
    ) -> tuple[list[AuthorMetadata], int]:
        """Filter authors by staleness if enabled.

        Parameters
        ----------
        all_authors : list[AuthorMetadata]
            List of all authors to filter.

        Returns
        -------
        tuple[list[AuthorMetadata], int]
            Tuple of (filtered_authors, skipped_count).
        """
        if self._stale_data_max_age_days is None:
            return all_authors, 0

        authors_to_process = []
        skipped_count = 0
        for author in all_authors:
            if self._should_skip_author(author):
                skipped_count += 1
                logger.debug(
                    "Skipping author '%s' (ID: %s) - has fresh similarities",
                    author.name,
                    author.id,
                )
            else:
                authors_to_process.append(author)

        if skipped_count > 0:
            logger.info(
                "Skipping %d authors with fresh similarities (out of %d total)",
                skipped_count,
                len(all_authors),
            )

        return authors_to_process, skipped_count

    def _process_author_pairs_loop(
        self,
        context: PipelineContext,
        authors_to_process: list[AuthorMetadata],
        processor: "AuthorPairProcessor",
        actual_total_pairs: int,
        skipped_count: int,
    ) -> int:
        """Process all author pairs in a loop.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        authors_to_process : list[AuthorMetadata]
            List of authors to process.
        processor : AuthorPairProcessor
            Processor for author pairs.
        actual_total_pairs : int
            Total number of pairs to process.
        skipped_count : int
            Number of skipped authors.

        Returns
        -------
        int
            Number of similarities created.
        """
        similarities_created = 0
        pairs_processed = 0

        for i, author1 in enumerate(authors_to_process):
            if context.check_cancelled():
                break

            for _j, author2 in enumerate(authors_to_process[i + 1 :], start=i + 1):
                if context.check_cancelled():
                    break

                if processor.process_pair(author1, author2):
                    similarities_created += 1
                    logger.debug(
                        "Created similarity between '%s' and '%s'",
                        author1.name,
                        author2.name,
                    )

                pairs_processed += 1

                # Update progress
                if self._progress_tracker is None:
                    msg = "Progress tracker must be initialized"
                    raise ValueError(msg)
                progress = self._progress_tracker.update(1)

                # Log progress periodically
                if self._progress_tracker.should_log():
                    logger.info(
                        "Score progress: %d/%d pairs processed (%d similarities created, %d authors skipped)",
                        pairs_processed,
                        actual_total_pairs,
                        similarities_created,
                        skipped_count,
                    )

                # Update progress with metadata
                metadata = {
                    "current_stage": {
                        "name": "score",
                        "status": "in_progress",
                        "current_index": pairs_processed,
                        "total_items": actual_total_pairs,
                        "similarities_created": similarities_created,
                        "authors_skipped": skipped_count,
                    },
                }
                context.update_progress(progress, metadata)

        return similarities_created

    def _process_all_author_pairs(
        self,
        context: PipelineContext,
        all_authors: list[AuthorMetadata],
    ) -> tuple[int, int]:
        """Process all author pairs and create similarities.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context.
        all_authors : list[AuthorMetadata]
            List of all authors to compare.

        Returns
        -------
        tuple[int, int]
            Tuple of (similarities_created, authors_skipped).
        """
        if self._similarity_calculator is None:
            self._similarity_calculator = self._create_default_calculator()

        if self._similarity_repository is None:
            msg = "Similarity repository must be initialized"
            raise ValueError(msg)

        processor = AuthorPairProcessor(
            self._similarity_calculator,
            self._similarity_repository,
            self._min_similarity,
        )

        # Filter out authors with fresh similarities if staleness check is enabled
        authors_to_process, skipped_count = self._filter_authors_by_staleness(
            all_authors
        )

        # Recalculate total pairs based on filtered authors
        actual_total_pairs = (
            len(authors_to_process) * (len(authors_to_process) - 1) // 2
        )

        self._progress_tracker = ProgressTracker(
            actual_total_pairs, log_interval=max(1, min(100, actual_total_pairs // 10))
        )

        similarities_created = self._process_author_pairs_loop(
            context,
            authors_to_process,
            processor,
            actual_total_pairs,
            skipped_count,
        )

        return similarities_created, skipped_count

    def execute(self, context: PipelineContext) -> StageResult:
        """Execute the score stage.

        Parameters
        ----------
        context : PipelineContext
            Pipeline context with ingested authors.

        Returns
        -------
        StageResult
            Result with similarity scores created.
        """
        if context.check_cancelled():
            return StageResult(success=False, message="Score cancelled")

        logger.info("Starting score stage for library %d", context.library_id)

        try:
            # Initialize repositories if needed
            self._create_repositories(context.session)

            # Get calculator if not set
            if self._similarity_calculator is None:
                self._similarity_calculator = self._create_default_calculator()

            # Get all authors
            self._ensure_author_repository_initialized()
            # Type narrowing: after _ensure_author_repository_initialized(),
            # _author_repository is guaranteed to be non-None
            author_repo = self._author_repository
            if author_repo is None:
                self._raise_repository_not_initialized_error()
            # Verify the repository has the get_all method and it's callable
            get_all_method = getattr(author_repo, "get_all", None)
            if get_all_method is None:
                self._raise_missing_get_all_method_error()
            if not callable(get_all_method):
                self._raise_missing_get_all_method_error()
            # Type narrowing: get_all_method is confirmed to be callable
            # Use the verified callable method
            all_authors = get_all_method(self._author_limit)  # type: ignore[call-overload]
            total_pairs = len(all_authors) * (len(all_authors) - 1) // 2

            logger.info(
                "Calculating similarities for %d authors (%d pairs) in library %d",
                len(all_authors),
                total_pairs,
                context.library_id,
            )

            if total_pairs == 0:
                logger.warning(
                    "No author pairs to score in library %d", context.library_id
                )
                return StageResult(
                    success=True,
                    message="No authors to score",
                    stats={"similarities_created": 0},
                )

            similarities_created, authors_skipped = self._process_all_author_pairs(
                context,
                all_authors,
            )

            # Commit similarities
            context.session.commit()

            stats = {
                "similarities_created": similarities_created,
                "pairs_processed": total_pairs,
                "authors_skipped": authors_skipped,
            }

            logger.info(
                "Created %d author similarities for library %d (%d authors skipped due to fresh similarities)",
                similarities_created,
                context.library_id,
                authors_skipped,
            )

            return StageResult(
                success=True,
                message=f"Created {similarities_created} author similarities",
                stats=stats,
            )

        except Exception as e:
            logger.exception("Error in score stage")
            context.session.rollback()
            return StageResult(
                success=False,
                message=f"Score failed: {e}",
            )
