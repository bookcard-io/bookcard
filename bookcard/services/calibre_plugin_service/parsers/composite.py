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

"""Composite parser for Calibre plugin output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookcard.services.calibre_plugin_service.models import PluginInfo
    from bookcard.services.calibre_plugin_service.parsers.base import (
        PluginOutputParser,
    )


@dataclass(frozen=True, slots=True)
class CompositeParser:
    """Try parsers in order and return the first match."""

    parsers: tuple[PluginOutputParser, ...]

    def parse(self, output: str) -> list[PluginInfo]:
        """Parse output into plugin info.

        Parameters
        ----------
        output : str
            Raw ``calibre-customize -l`` stdout.

        Returns
        -------
        list[PluginInfo]
            Parsed plugins.
        """
        if not output.strip():
            return []

        for parser in self.parsers:
            if parser.can_parse(output):
                return parser.parse(output)

        return []
