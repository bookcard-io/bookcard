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

"""Record processors for OpenLibrary dump ingestion.

Each processor handles a specific record type, following the Single
Responsibility Principle.
"""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

from fundamental.models.openlibrary import (
    OpenLibraryAuthor,
    OpenLibraryAuthorWork,
    OpenLibraryEdition,
    OpenLibraryEditionIsbn,
    OpenLibraryWork,
)
from fundamental.services.tasks.openlibrary.batch import BatchProcessor
from fundamental.services.tasks.openlibrary.models import DumpRecord

ModelT = TypeVar("ModelT")


class RecordProcessor[ModelT](ABC):
    """Abstract base class for processing specific record types.

    Follows the Open/Closed Principle - new record types can be added
    by implementing this interface without modifying existing code.
    """

    @abstractmethod
    def can_process(self, record: DumpRecord) -> bool:
        """Check if this processor can handle the record.

        Parameters
        ----------
        record : DumpRecord
            Record to check.

        Returns
        -------
        bool
            True if this processor can handle the record.
        """
        ...

    @abstractmethod
    def process_record(self, record: DumpRecord) -> list[ModelT]:
        """Process a single record into model objects.

        Parameters
        ----------
        record : DumpRecord
            Record to process.

        Returns
        -------
        list[ModelT]
            List of model objects created from the record.
        """
        ...


class AuthorRecordProcessor(RecordProcessor[OpenLibraryAuthor]):
    """Processes author records.

    Converts dump records into OpenLibraryAuthor model objects.
    """

    def can_process(self, record: DumpRecord) -> bool:
        """Check if this is an author record.

        Parameters
        ----------
        record : DumpRecord
            Record to check.

        Returns
        -------
        bool
            True if record key starts with '/authors/'.
        """
        return record.key.startswith("/authors/")

    def process_record(self, record: DumpRecord) -> list[OpenLibraryAuthor]:
        """Process author record.

        Parameters
        ----------
        record : DumpRecord
            Author record to process.

        Returns
        -------
        list[OpenLibraryAuthor]
            List containing a single OpenLibraryAuthor object.
        """
        author = OpenLibraryAuthor(
            type=record.record_type,
            key=record.key,
            revision=record.revision,
            last_modified=record.last_modified,
            data=record.data,
        )
        return [author]


class WorkRecordProcessor(RecordProcessor[OpenLibraryWork]):
    """Processes work records and extracts author-work relationships.

    Converts dump records into OpenLibraryWork model objects and
    extracts author-work relationships for batch processing.
    """

    def __init__(
        self, author_work_batch: BatchProcessor[OpenLibraryAuthorWork]
    ) -> None:
        """Initialize work record processor.

        Parameters
        ----------
        author_work_batch : BatchProcessor[OpenLibraryAuthorWork]
            Batch processor for author-work relationships.
        """
        self.author_work_batch = author_work_batch

    def can_process(self, record: DumpRecord) -> bool:
        """Check if this is a work record.

        Parameters
        ----------
        record : DumpRecord
            Record to check.

        Returns
        -------
        bool
            True if record key starts with '/works/'.
        """
        return record.key.startswith("/works/")

    def process_record(self, record: DumpRecord) -> list[OpenLibraryWork]:
        """Process work record and extract author relationships.

        Parameters
        ----------
        record : DumpRecord
            Work record to process.

        Returns
        -------
        list[OpenLibraryWork]
            List containing a single OpenLibraryWork object.
        """
        work = OpenLibraryWork(
            type=record.record_type,
            key=record.key,
            revision=record.revision,
            last_modified=record.last_modified,
            data=record.data,
        )

        # Extract author-work relationships
        author_works = self._extract_author_works(record.data, record.key)
        if author_works:
            self.author_work_batch.add(author_works)

        return [work]

    def _extract_author_works(
        self, data: dict[str, Any], work_key: str
    ) -> list[OpenLibraryAuthorWork]:
        """Extract author-works relationships from work data.

        Deduplicates author-work pairs to prevent unique constraint violations.

        Parameters
        ----------
        data : dict[str, Any]
            Work data dictionary.
        work_key : str
            Work key identifier.

        Returns
        -------
        list[OpenLibraryAuthorWork]
            List of unique author-work relationships.
        """
        author_works = []
        seen_pairs: set[tuple[str, str]] = set()
        authors = data.get("authors", [])

        if isinstance(authors, list):
            for author_ref in authors:
                if isinstance(author_ref, dict):
                    author_obj = author_ref.get("author")
                    # Handle both dict format {"author": {"key": "/authors/OL123A"}}
                    # and string format {"author": "/authors/OL123A"}
                    if isinstance(author_obj, dict):
                        author_key = author_obj.get("key")
                    elif isinstance(author_obj, str):
                        author_key = author_obj
                    else:
                        author_key = None

                    if author_key and isinstance(author_key, str):
                        pair = (author_key, work_key)
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            author_works.append(
                                OpenLibraryAuthorWork(
                                    author_key=author_key, work_key=work_key
                                )
                            )
        return author_works


class EditionRecordProcessor(RecordProcessor[OpenLibraryEdition]):
    """Processes edition records and extracts ISBNs.

    Converts dump records into OpenLibraryEdition model objects and
    extracts ISBNs for batch processing.
    """

    def __init__(self, isbn_batch: BatchProcessor[OpenLibraryEditionIsbn]) -> None:
        """Initialize edition record processor.

        Parameters
        ----------
        isbn_batch : BatchProcessor[OpenLibraryEditionIsbn]
            Batch processor for ISBNs.
        """
        self.isbn_batch = isbn_batch

    def can_process(self, record: DumpRecord) -> bool:
        """Check if this is an edition record.

        Parameters
        ----------
        record : DumpRecord
            Record to check.

        Returns
        -------
        bool
            True if record key starts with '/editions/'.
        """
        return record.key.startswith("/editions/")

    def process_record(self, record: DumpRecord) -> list[OpenLibraryEdition]:
        """Process edition record and extract ISBNs.

        Parameters
        ----------
        record : DumpRecord
            Edition record to process.

        Returns
        -------
        list[OpenLibraryEdition]
            List containing a single OpenLibraryEdition object.
        """
        work_key = self._extract_work_key(record.data)

        edition = OpenLibraryEdition(
            type=record.record_type,
            key=record.key,
            revision=record.revision,
            last_modified=record.last_modified,
            data=record.data,
            work_key=work_key,
        )

        # Extract ISBNs
        isbns = self._extract_isbns(record.data, record.key)
        if isbns:
            self.isbn_batch.add(isbns)

        return [edition]

    def _extract_work_key(self, data: dict[str, Any]) -> str | None:
        """Extract work key from edition data.

        Handles both dict format {"works": [{"key": "/works/OL123W"}]}
        and string format {"works": ["/works/OL123W"]}.

        Parameters
        ----------
        data : dict[str, Any]
            Edition data dictionary.

        Returns
        -------
        str | None
            Work key if found, None otherwise.
        """
        works = data.get("works", [])
        if isinstance(works, list) and len(works) > 0:
            work_ref = works[0]
            # Handle both dict format {"key": "/works/OL123W"}
            # and string format "/works/OL123W"
            if isinstance(work_ref, dict):
                return work_ref.get("key")
            if isinstance(work_ref, str):
                return work_ref
        return None

    def _extract_isbns(
        self, data: dict[str, Any], edition_key: str
    ) -> list[OpenLibraryEditionIsbn]:
        """Extract ISBNs from edition data.

        Deduplicates ISBNs to prevent unique constraint violations.
        The same ISBN may appear in multiple fields (isbn_13, isbn_10, isbn).

        Parameters
        ----------
        data : dict[str, Any]
            Edition data dictionary.
        edition_key : str
            Edition key identifier.

        Returns
        -------
        list[OpenLibraryEditionIsbn]
            List of unique ISBN objects.
        """
        isbns = []
        seen_isbns: set[str] = set()
        isbn_fields = ["isbn_13", "isbn_10", "isbn"]

        for isbn_field in isbn_fields:
            isbn_list = data.get(isbn_field, [])
            if isinstance(isbn_list, list):
                for isbn in isbn_list:
                    if isinstance(isbn, str):
                        isbn_clean = isbn.strip()
                        if isbn_clean and isbn_clean not in seen_isbns:
                            seen_isbns.add(isbn_clean)
                            isbns.append(
                                OpenLibraryEditionIsbn(
                                    edition_key=edition_key, isbn=isbn_clean
                                )
                            )
        return isbns
