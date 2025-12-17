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

"""Plugin list output parsing strategies."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from bookcard.services.calibre_plugin_service.models import PluginInfo


class PluginOutputParser(Protocol):
    """Parse ``calibre-customize -l`` output."""

    def can_parse(self, output: str) -> bool:
        """Return True if this parser can handle the output."""

    def parse(self, output: str) -> list[PluginInfo]:
        """Parse output into plugin info."""


def extract_author(description: str) -> str:
    """Best-effort author extraction from a plugin description."""
    if not description:
        return ""

    m = re.search(r"Credit given to\s+(.+?)(?:\s+for\s+|\.|$)", description, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip())

    m = re.search(r"Author[:\s]+(.+?)(?:\.|,|;|$)", description, re.I)
    if m:
        return re.sub(r"\s+", " ", m.group(1).strip())

    return ""
