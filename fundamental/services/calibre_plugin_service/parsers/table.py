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

"""Parser for the newer table format output."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fundamental.services.calibre_plugin_service.parsers.base import extract_author

if TYPE_CHECKING:
    from collections.abc import Callable

    from fundamental.services.calibre_plugin_service.models import PluginInfo


@dataclass(frozen=True, slots=True)
class TableFormatParser:
    """Parse the table format emitted by ``calibre-customize -l``.

    Parameters
    ----------
    user_plugin_names : Callable[[], set[str]]
        Provider for user-installed plugin name stems.
    """

    user_plugin_names: Callable[[], set[str]]

    def can_parse(self, output: str) -> bool:
        """Return True if output looks like the table format.

        Parameters
        ----------
        output : str
            Raw ``calibre-customize -l`` output.

        Returns
        -------
        bool
            True if the table parser should be used.
        """
        first = next((ln for ln in output.splitlines() if ln.strip()), "")
        return first.startswith("Type") and "Name" in first

    def parse(self, output: str) -> list[PluginInfo]:
        """Parse table-format output into plugin info.

        Parameters
        ----------
        output : str
            Raw ``calibre-customize -l`` output.

        Returns
        -------
        list[PluginInfo]
            Parsed plugins.
        """
        installed = {n.lower() for n in self.user_plugin_names()}
        lines = output.splitlines()

        row_re = re.compile(
            r"^(?P<type>.+?)\s{2,}(?P<name>.+?)\s+\((?P<version>[^)]+)\)\s+(?P<disabled>True|False)\b"
        )

        plugins: list[PluginInfo] = []
        i = 0
        while i < len(lines):
            s = lines[i].strip()
            if not s or s.startswith(("Type", "---")):
                i += 1
                continue

            m = row_re.match(s)
            if not m:
                i += 1
                continue

            name = m.group("name").strip()
            version = m.group("version").strip()

            desc_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                desc = lines[i].strip()
                if desc:
                    desc_lines.append(desc)
                i += 1

            description = " ".join(desc_lines).strip()

            if installed and name.lower() not in installed:
                continue

            author = extract_author(description) or "Unknown"
            plugins.append({
                "name": name,
                "version": version,
                "author": author,
                "description": description,
            })

        return plugins
