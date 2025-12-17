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

"""Metadata merging service.

Merges multiple metadata records into one.
Follows SRP by focusing solely on merging logic.
Follows DRY by consolidating duplicate merge patterns.
"""

from dataclasses import dataclass
from enum import StrEnum

from bookcard.models.metadata import MetadataRecord


class MergeStrategy(StrEnum):
    """Metadata merge strategy.

    Attributes
    ----------
    MERGE_BEST : str
        Merge from high-scoring records (within threshold of best).
    FIRST_WINS : str
        Use only the first (highest-scoring) record.
    LAST_WINS : str
        Use only the last (lowest-scoring) record.
    MERGE_ALL : str
        Merge from all records regardless of score.
    """

    MERGE_BEST = "merge_best"
    FIRST_WINS = "first_wins"
    LAST_WINS = "last_wins"
    MERGE_ALL = "merge_all"


@dataclass
class ScoredMetadataRecord:
    """Metadata record with a quality score.

    Attributes
    ----------
    record : MetadataRecord
        Metadata record.
    score : float
        Quality score (0.0-1.0).
    """

    record: MetadataRecord
    score: float


class MetadataMerger:
    """Merges multiple metadata records into one.

    Takes the best fields from multiple records based on scoring.
    Separates merging concerns from fetching/scoring logic.
    """

    def __init__(
        self,
        strategy: MergeStrategy | str = MergeStrategy.MERGE_BEST,
        score_threshold_ratio: float = 0.8,
    ) -> None:
        """Initialize metadata merger.

        Parameters
        ----------
        strategy : MergeStrategy | str
            Merge strategy to use (default: MERGE_BEST).
        score_threshold_ratio : float
            Only merge from records with score within this ratio of best
            (default: 0.8, meaning 80% of best score).
            Only used for MERGE_BEST strategy.
        """
        if isinstance(strategy, str):
            try:
                self._strategy = MergeStrategy(strategy)
            except ValueError:
                self._strategy = MergeStrategy.MERGE_BEST
        else:
            self._strategy = strategy
        self._score_threshold_ratio = score_threshold_ratio

    def merge(
        self,
        scored_records: list[ScoredMetadataRecord],
    ) -> MetadataRecord:
        """Merge metadata from multiple scored records.

        Uses strategy-specific logic to merge records.

        Parameters
        ----------
        scored_records : list[ScoredMetadataRecord]
            List of scored metadata records (should be sorted by score).

        Returns
        -------
        MetadataRecord
            Merged metadata record.

        Raises
        ------
        ValueError
            If scored_records is empty.
        """
        if not scored_records:
            msg = "Cannot merge empty record list"
            raise ValueError(msg)

        if self._strategy == MergeStrategy.FIRST_WINS:
            return self._merge_first_wins(scored_records)
        if self._strategy == MergeStrategy.LAST_WINS:
            return self._merge_last_wins(scored_records)
        if self._strategy == MergeStrategy.MERGE_ALL:
            return self._merge_all(scored_records)
        # Default strategy is MERGE_BEST
        return self._merge_best(scored_records)

    def _merge_best(self, scored_records: list[ScoredMetadataRecord]) -> MetadataRecord:
        """Merge using best strategy (high-scoring records only).

        Uses highest-scoring record as base, then merges fields from
        other high-scoring records within threshold.

        Parameters
        ----------
        scored_records : list[ScoredMetadataRecord]
            List of scored metadata records (should be sorted by score).

        Returns
        -------
        MetadataRecord
            Merged metadata record.
        """
        # Use highest-scoring record as base
        best_record = scored_records[0].record
        merged = self._initialize_merged_record(best_record)

        # Merge from other high-scoring records
        best_score = scored_records[0].score
        for scored in scored_records[1:]:
            # Only merge from records with score within threshold of best
            if scored.score < best_score * self._score_threshold_ratio:
                break
            self._merge_record_into_merged(scored.record, merged)

        return merged

    def _merge_first_wins(
        self, scored_records: list[ScoredMetadataRecord]
    ) -> MetadataRecord:
        """Merge using first wins strategy (first record only).

        Uses only the first (highest-scoring) record.

        Parameters
        ----------
        scored_records : list[ScoredMetadataRecord]
            List of scored metadata records (should be sorted by score).

        Returns
        -------
        MetadataRecord
            First metadata record.
        """
        return self._initialize_merged_record(scored_records[0].record)

    def _merge_last_wins(
        self, scored_records: list[ScoredMetadataRecord]
    ) -> MetadataRecord:
        """Merge using last wins strategy (last record only).

        Uses only the last (lowest-scoring) record.

        Parameters
        ----------
        scored_records : list[ScoredMetadataRecord]
            List of scored metadata records (should be sorted by score).

        Returns
        -------
        MetadataRecord
            Last metadata record.
        """
        return self._initialize_merged_record(scored_records[-1].record)

    def _merge_all(self, scored_records: list[ScoredMetadataRecord]) -> MetadataRecord:
        """Merge using merge all strategy (all records).

        Uses highest-scoring record as base, then merges fields from
        all other records regardless of score.

        Parameters
        ----------
        scored_records : list[ScoredMetadataRecord]
            List of scored metadata records (should be sorted by score).

        Returns
        -------
        MetadataRecord
            Merged metadata record.
        """
        # Use highest-scoring record as base
        best_record = scored_records[0].record
        merged = self._initialize_merged_record(best_record)

        # Merge from all other records
        for scored in scored_records[1:]:
            self._merge_record_into_merged(scored.record, merged)

        return merged

    def _initialize_merged_record(self, base_record: MetadataRecord) -> MetadataRecord:
        """Initialize merged record from base record.

        Parameters
        ----------
        base_record : MetadataRecord
            Base record to initialize from.

        Returns
        -------
        MetadataRecord
            Initialized merged record.
        """
        return MetadataRecord(
            source_id=base_record.source_id,
            external_id=base_record.external_id,
            title=base_record.title,
            authors=list(base_record.authors) if base_record.authors else [],
            url=base_record.url,
            cover_url=base_record.cover_url,
            description=base_record.description or "",
            series=base_record.series,
            series_index=base_record.series_index,
            identifiers=(
                dict(base_record.identifiers) if base_record.identifiers else {}
            ),
            publisher=base_record.publisher,
            published_date=base_record.published_date,
            rating=base_record.rating,
            languages=list(base_record.languages) if base_record.languages else [],
            tags=list(base_record.tags) if base_record.tags else [],
        )

    def _merge_record_into_merged(
        self, record: MetadataRecord, merged: MetadataRecord
    ) -> None:
        """Merge a record into the merged record.

        Uses generic merge utilities to avoid duplication.

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update (mutated).
        """
        # Merge list fields (authors, languages, tags)
        self._merge_list_field(record.authors, merged.authors)
        self._merge_list_field(record.languages, merged.languages)
        self._merge_list_field(record.tags, merged.tags)

        # Merge description (take longest)
        self._merge_description(record, merged)

        # Merge cover URL (prefer first non-empty from higher-scored source)
        self._merge_cover_url(record, merged)

        # Merge identifiers (union)
        self._merge_identifiers(record, merged)

        # Merge "first non-empty wins" fields
        for field_name in ["series", "publisher", "published_date"]:
            self._merge_first_value(record, merged, field_name)

        # Special handling for series_index (copy when series is set)
        if record.series and not merged.series:
            merged.series_index = record.series_index

        # Merge rating (take highest)
        self._merge_rating(record, merged)

    def _merge_list_field(
        self, source_list: list[str] | None, target_list: list[str]
    ) -> None:
        """Merge items from source into target, avoiding duplicates.

        Generic utility for merging list fields (authors, languages, tags).

        Parameters
        ----------
        source_list : list[str] | None
            Source list to merge from.
        target_list : list[str]
            Target list to merge into (mutated).
        """
        if source_list:
            for item in source_list:
                if item not in target_list:
                    target_list.append(item)

    def _merge_description(
        self, record: MetadataRecord, merged: MetadataRecord
    ) -> None:
        """Merge description from record into merged.

        Takes the longest description.

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update.
        """
        if record.description and len(record.description) > len(
            merged.description or ""
        ):
            merged.description = record.description

    def _merge_cover_url(self, record: MetadataRecord, merged: MetadataRecord) -> None:
        """Merge cover URL from record into merged.

        Prefers first non-empty cover URL from higher-scored source.
        (Records are already sorted by score, so first wins.)

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update.
        """
        if record.cover_url and not merged.cover_url:
            merged.cover_url = record.cover_url

    def _merge_identifiers(
        self, record: MetadataRecord, merged: MetadataRecord
    ) -> None:
        """Merge identifiers from record into merged.

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update.
        """
        if record.identifiers:
            merged.identifiers.update(record.identifiers)

    def _merge_first_value(
        self,
        record: MetadataRecord,
        merged: MetadataRecord,
        field_name: str,
    ) -> None:
        """Set field on merged if empty and source has value.

        Generic utility for "first non-empty wins" pattern.

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update.
        field_name : str
            Name of field to merge.
        """
        source_value = getattr(record, field_name, None)
        merged_value = getattr(merged, field_name, None)
        if source_value and not merged_value:
            setattr(merged, field_name, source_value)

    def _merge_rating(self, record: "MetadataRecord", merged: "MetadataRecord") -> None:
        """Merge rating from record into merged.

        Takes the highest rating.

        Parameters
        ----------
        record : MetadataRecord
            Record to merge from.
        merged : MetadataRecord
            Merged record to update.
        """
        if record.rating is not None and (
            merged.rating is None or record.rating > merged.rating
        ):
            merged.rating = record.rating
