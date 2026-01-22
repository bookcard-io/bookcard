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

"""Default wiring for the email-send task.

This module acts as a composition root and may import concrete implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookcard.services.tasks.email_send.dependencies import EmailSendDependencies
from bookcard.services.tasks.email_send.implementations import (
    DefaultEmailSendBookServiceFactory,
    DefaultEmailServiceFactory,
    DefaultLibraryProvider,
)
from bookcard.services.tasks.email_send.preparation import DefaultSendPreparationService
from bookcard.services.tasks.email_send.preprocessing import PreprocessingPipeline

if TYPE_CHECKING:
    from sqlmodel import Session


def create_default_email_send_dependencies(
    session: Session,  # type: ignore[type-arg]
    encryption_key: str,
) -> EmailSendDependencies:
    """Create default dependencies for the email-send task.

    Parameters
    ----------
    session : Session
        Database session (unused, kept for API compatibility).
    encryption_key : str
        Encryption key for decrypting email configuration.

    Returns
    -------
    EmailSendDependencies
        Default dependencies container.
    """
    _ = session  # Kept for API compatibility with dependency factories.
    return EmailSendDependencies(
        library_provider=DefaultLibraryProvider(),
        email_service_factory=DefaultEmailServiceFactory(encryption_key),
        book_service_factory=DefaultEmailSendBookServiceFactory(),
        preparation_service=DefaultSendPreparationService(),
        preprocessing_pipeline=PreprocessingPipeline.default(),
    )
