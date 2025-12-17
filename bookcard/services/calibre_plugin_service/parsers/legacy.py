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

"""Parser for the legacy human-readable format output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookcard.services.calibre_plugin_service.models import PluginInfo


@dataclass(frozen=True, slots=True)
class LegacyFormatParser:
    """Parse legacy output like ``Name (Version) by Author``."""

    def can_parse(self, output: str) -> bool:
        """Return True as a fallback parser.

        Parameters
        ----------
        output : str
            Raw output (unused).

        Returns
        -------
        bool
            Always True.
        """
        del output
        return True

    def parse(self, output: str) -> list[PluginInfo]:
        """Parse legacy output into plugin info.

        Parameters
        ----------
        output : str
            Raw ``calibre-customize -l`` output.

        Returns
        -------
        list[PluginInfo]
            Parsed plugins.
        """
        plugins: list[PluginInfo] = []
        current: PluginInfo | None = None

        for raw in output.splitlines():
            s = raw.strip()
            if not s:
                continue

            if " (" in s and ") by " in s:
                if current:
                    plugins.append(current)

                name_part, rest = s.split(" (", 1)
                version_part, author_part = rest.split(") by ", 1)
                current = {
                    "name": name_part.strip(),
                    "version": version_part.strip(),
                    "author": author_part.strip(),
                    "description": "",
                }
                continue

            if current:
                current["description"] = (
                    f"{current['description']} {s}".strip()
                    if current["description"]
                    else s
                )

        if current:
            plugins.append(current)

        return plugins
