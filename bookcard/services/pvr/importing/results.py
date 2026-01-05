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

"""Import result data structures."""

from dataclasses import dataclass, field
from enum import Enum


class ImportStatus(Enum):
    """Status of an import operation."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ImportResult:
    """Result of an import operation."""

    status: ImportStatus
    book_id: int | None = None
    error_message: str | None = None
    files_processed: int = 0
    files_failed: int = 0

    @property
    def is_success(self) -> bool:
        """Check if import was successful."""
        return self.status == ImportStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        """Check if import has errors."""
        return self.error_message is not None


@dataclass
class ImportBatchResult:
    """Results from batch import operation."""

    successful: int = 0
    failed: int = 0
    skipped: int = 0
    errors: dict[int, str] = field(default_factory=dict)

    def add_result(self, result: ImportResult, item_id: int | None = None) -> None:
        """Add a single result to the batch."""
        if result.status == ImportStatus.SUCCESS:
            self.successful += 1
        elif result.status == ImportStatus.FAILED:
            self.failed += 1
            if item_id is not None and result.error_message:
                self.errors[item_id] = result.error_message
        else:
            self.skipped += 1

    def add_failed(self, item_id: int, error: str) -> None:
        """Add a failed item directly."""
        self.failed += 1
        self.errors[item_id] = error

    @property
    def total_processed(self) -> int:
        """Total number of items processed."""
        return self.successful + self.failed + self.skipped


@dataclass
class FileGroupImportResult:
    """Result of importing a file group."""

    book_id: int | None = None
    main_file_added: bool = False
    formats_added: int = 0
    formats_failed: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class FileRecordingResult:
    """Result of file recording operation."""

    success: bool
    error: Exception | None = None


@dataclass
class WorkflowResult:
    """Result of the import workflow."""

    book_id: int | None

    @property
    def success(self) -> bool:
        """Check if workflow was successful (book ID present)."""
        return self.book_id is not None


@dataclass
class ValidationResult:
    """Result of validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)

    @property
    def error_message(self) -> str | None:
        """Get combined error message."""
        return "; ".join(self.errors) if self.errors else None


@dataclass
class FreshIngestResult:
    """Result of fresh ingest operation."""

    book_id: int | None
    error: str | None = None

    @property
    def success(self) -> bool:
        """Check if fresh ingest was successful."""
        return self.book_id is not None


class FormatAddDecision(Enum):
    """Decision on whether to add a format."""

    ADD_NEW = "add_new"
    UPDATE_DIFFERENT = "update_different"
    SKIP_IDENTICAL = "skip_identical"


@dataclass
class FormatCheckResult:
    """Result of checking if format should be added."""

    decision: FormatAddDecision

    @property
    def should_add(self) -> bool:
        """Check if format should be added based on decision."""
        return self.decision in (
            FormatAddDecision.ADD_NEW,
            FormatAddDecision.UPDATE_DIFFERENT,
        )
