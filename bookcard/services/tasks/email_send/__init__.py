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

"""Email send task module.

Refactored to follow SOLID principles with dependency injection,
value objects, and separation of concerns.
"""

from bookcard.services.tasks.email_send.domain import (
    BookId,
    EmailTarget,
    EncryptionKey,
    FileFormat,
    SendBookRequest,
    SendMetadata,
    SendPreparation,
)
from bookcard.services.tasks.email_send.task import EmailSendTask

__all__ = [
    "BookId",
    "EmailSendTask",
    "EmailTarget",
    "EncryptionKey",
    "FileFormat",
    "SendBookRequest",
    "SendMetadata",
    "SendPreparation",
]
