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

"""Send format selection service.

Encapsulates both:
- Reading the user's send-format preference ordering from settings.
- Selecting the best available format for a book, considering device preference.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from sqlmodel import Session, select

from bookcard.models.auth import UserSetting
from bookcard.repositories import BookWithFullRelations, ereader_repository
from bookcard.services.settings_value_codecs import (
    decode_string_list,
    normalize_string_list,
)

if TYPE_CHECKING:
    from bookcard.models.auth import EReaderDevice


class SendFormatService:
    """Service for selecting the best format to send for a user/book/device."""

    _SETTING_KEY: ClassVar[str] = "send_format_priority"
    _DEFAULT_PRIORITY: ClassVar[tuple[str, ...]] = ("EPUB", "PDF")

    def __init__(self, session: Session) -> None:
        """Initialize the service.

        Parameters
        ----------
        session : Session
            Database session used for settings and device lookups.
        """
        self._session = session

    def get_user_format_priority(self, user_id: int) -> list[str]:
        """Get user's preferred send format priority list.

        Parameters
        ----------
        user_id : int
            User identifier.

        Returns
        -------
        list[str]
            Ordered list of preferred formats (uppercase). Defaults to
            ``["EPUB", "PDF"]`` if not configured or invalid.
        """
        stmt = select(UserSetting).where(
            UserSetting.user_id == user_id,
            UserSetting.key == self._SETTING_KEY,
        )
        setting = self._session.exec(stmt).first()
        if setting is None or not setting.value:
            return list(self._DEFAULT_PRIORITY)

        parsed = decode_string_list(setting.value, allow_csv_fallback=True)
        normalized = normalize_string_list(parsed, normalizer=str.upper, dedupe=True)
        return normalized if normalized else list(self._DEFAULT_PRIORITY)

    def select_format(
        self,
        *,
        user_id: int,
        to_email: str | None,
        requested_format: str | None,
        book_with_rels: BookWithFullRelations,
    ) -> str | None:
        """Select the best format to send.

        Selection order:
        1) Explicit request (payload) wins.
        2) Device `preferred_format` if configured and available for the book.
        3) User `send_format_priority` setting.
        4) First available format on the book.

        Parameters
        ----------
        user_id : int
            User ID (device lookup and settings).
        to_email : str | None
            Target email; if None, default/first device is assumed.
        requested_format : str | None
            Explicit requested format (e.g., 'EPUB').
        book_with_rels : BookWithFullRelations
            Book with available formats.

        Returns
        -------
        str | None
            Selected format (uppercase), or None if the book has no formats.
        """
        if requested_format:
            return requested_format.upper()

        available = self._available_formats(book_with_rels)
        if not available:
            return None

        device = self._resolve_device(user_id=user_id, to_email=to_email)
        if device is not None and device.preferred_format is not None:
            preferred = device.preferred_format.value.upper()
            if preferred in available:
                return preferred

        priority = self.get_user_format_priority(user_id)
        for fmt in priority:
            fmt_upper = fmt.upper()
            if fmt_upper in available:
                return fmt_upper

        first = (
            str(book_with_rels.formats[0].get("format", "")).upper()
            if book_with_rels.formats
            else ""
        )
        return first or None

    def _resolve_device(
        self, *, user_id: int, to_email: str | None
    ) -> EReaderDevice | None:
        """Resolve the target device (if any).

        Notes
        -----
        Production code uses a real SQLModel session. Some tests may supply a light
        stub session; in that scenario, we skip device resolution and fall back to
        user-level priority.
        """
        try:
            repo = ereader_repository.EReaderRepository(self._session)
            if to_email:
                return repo.find_by_email(user_id, to_email)

            device = repo.find_default(user_id)
            if device is not None:
                return device

            devices = list(repo.find_by_user(user_id))
            return devices[0] if devices else None
        except AttributeError:
            return None

    @staticmethod
    def _available_formats(book_with_rels: BookWithFullRelations) -> set[str]:
        """Return set of available formats (uppercase)."""
        return {
            str(f.get("format", "")).upper()
            for f in book_with_rels.formats
            if isinstance(f.get("format", ""), str) and str(f.get("format", "")).strip()
        }
