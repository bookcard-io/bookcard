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

"""Validation for PVR import."""

import logging
from typing import Protocol

from bookcard.models.pvr import (
    DownloadItem,
    DownloadItemStatus,
    TrackedBookStatus,
)
from bookcard.services.pvr.importing.results import ValidationResult

logger = logging.getLogger(__name__)


class DownloadItemValidator(Protocol):
    """Protocol for download item validators."""

    def validate(self, item: DownloadItem) -> ValidationResult:
        """Validate download item.

        Parameters
        ----------
        item : DownloadItem
            The item to validate.

        Returns
        -------
        ValidationResult
            The validation result.
        """
        ...


class CompletionStatusValidator:
    """Validates download completion status."""

    def validate(self, item: DownloadItem) -> ValidationResult:
        """Validate that download status is COMPLETED."""
        if item.status != DownloadItemStatus.COMPLETED:
            return ValidationResult(False, [f"Download not completed: {item.status}"])
        return ValidationResult(True)


class FilePathValidator:
    """Validates file path exists."""

    def validate(self, item: DownloadItem) -> ValidationResult:
        """Validate that download item has a file path."""
        if not item.file_path:
            return ValidationResult(False, ["No file path specified"])
        return ValidationResult(True)


class TrackedBookStateValidator:
    """Validates tracked book state."""

    def validate(self, item: DownloadItem) -> ValidationResult:
        """Validate tracked book state for re-import or update."""
        if item.tracked_book.status == TrackedBookStatus.COMPLETED:
            if not item.tracked_book.matched_book_id:
                logger.info(
                    "Tracked book %d is marked completed but has no matched book. Proceeding with re-import.",
                    item.tracked_book.id,
                )
            elif item.tracked_book.matched_book_id:
                logger.info(
                    "Tracked book %d is already completed (linked to %d). Checking for updates.",
                    item.tracked_book.id,
                    item.tracked_book.matched_book_id,
                )
            # Allow to proceed
        return ValidationResult(True)


class CompositeValidator:
    """Combines multiple validators."""

    def __init__(self, validators: list[DownloadItemValidator]) -> None:
        """Initialize composite validator.

        Parameters
        ----------
        validators : list[DownloadItemValidator]
            List of validators to execute.
        """
        self._validators = validators

    def validate(self, item: DownloadItem) -> ValidationResult:
        """Run all validators in sequence.

        Parameters
        ----------
        item : DownloadItem
            The item to validate.

        Returns
        -------
        ValidationResult
            The validation result.
        """
        for validator in self._validators:
            result = validator.validate(item)
            if not result.is_valid:
                # We could stop early, but collecting all errors is often better
                # If we want to fail fast, we can break here
                return ValidationResult(False, result.errors)

        return ValidationResult(True)
