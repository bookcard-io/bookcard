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

"""Text cleaning utilities for DNB provider.

This module handles text normalization and cleaning for German text,
following Single Responsibility Principle.
"""

from __future__ import annotations

import re
from typing import ClassVar


class TextCleaner:
    """Text cleaning utilities for German text.

    This class is responsible solely for cleaning and normalizing text
    extracted from DNB records, including removal of sorting characters,
    title cleaning, series cleaning, and author name normalization.
    """

    # Unwanted series name patterns (common German publisher series)
    UNWANTED_SERIES_PATTERNS: ClassVar[list[str]] = [
        r"^Roman$",
        r"^Science-fiction$",
        r"^\[Ariadne\]$",
        r"^Ariadne$",
        r"^atb$",
        r"^BvT$",
        r"^Bastei L",
        r"^bb$",
        r"^Beck Paperback",
        r"^Beck\-.*berater",
        r"^Beck'sche Reihe",
        r"^Bibliothek Suhrkamp$",
        r"^BLT$",
        r"^DLV-Taschenbuch$",
        r"^Edition Suhrkamp$",
        r"^Edition Lingen Stiftung$",
        r"^Edition C",
        r"^Edition Metzgenstein$",
        r"^ETB$",
        r"^dtv",
        r"^Ein Goldmann",
        r"^Oettinger-Taschenbuch$",
        r"^Haymon-Taschenbuch$",
        r"^Mira Taschenbuch$",
        r"^Suhrkamp-Taschenbuch$",
        r"^Bastei-L",
        r"^Hey$",
        r"^btb$",
        r"^bt-Kinder",
        r"^Ravensburger",
        r"^Sammlung Luchterhand$",
        r"^blanvalet$",
        r"^KiWi$",
        r"^Piper$",
        r"^C.H. Beck",
        r"^Rororo",
        r"^Goldmann$",
        r"^Moewig$",
        r"^Fischer Klassik$",
        r"^hey! shorties$",
        r"^Ullstein",
        r"^Unionsverlag",
        r"^Ariadne-Krimi",
        r"^C.-Bertelsmann",
        r"^Phantastische Bibliothek$",
        r"^Knaur",
        r"^Volk-und-Welt",
        r"^Allgemeine",
        r"^Premium",
        r"^Horror-Bibliothek$",
    ]

    def remove_sorting_characters(self, text: str | None) -> str | None:
        """Remove sorting word markers from text.

        Removes characters with ordinals 152 and 156, which are
        used as sorting markers in German library catalogs.

        Parameters
        ----------
        text : str | None
            Text to clean.

        Returns
        -------
        str | None
            Cleaned text, or None if input was None.
        """
        if text is None:
            return None
        if text == "":
            return ""
        return "".join(c for c in text if ord(c) not in (152, 156))

    def clean_title(self, title: str | None) -> str:
        """Clean up book title.

        Removes translator information and sorting characters.

        Parameters
        ----------
        title : str | None
            Raw title.

        Returns
        -------
        str
            Cleaned title, or empty string if input was None.
        """
        if not title:
            return ""

        title = self.remove_sorting_characters(title) or ""

        # Remove name of translator from title
        # Pattern: "Title / Aus dem [language] von [translator]"  # noqa: ERA001
        match = re.search(
            r"^(.+) [/:] [Aa]us dem .+? von(\s\w+)+$",
            title,
        )
        if match:
            title = match.group(1)

        return title.strip()

    def clean_author_name(self, author: str) -> str:
        """Clean and normalize author name.

        Removes sorting characters and converts "Last, First" to "First Last".

        Parameters
        ----------
        author : str
            Raw author name.

        Returns
        -------
        str
            Cleaned author name.
        """
        author = self.remove_sorting_characters(author) or ""
        # Convert "Last, First" to "First Last"
        author = re.sub(r"^(.+), (.+)$", r"\2 \1", author)
        return author.strip()

    def clean_series(
        self,
        series: str | None,
        publisher_name: str | None = None,
    ) -> str | None:
        """Clean up series name.

        Removes sorting characters, filters out publisher names,
        and checks against unwanted series patterns.

        Parameters
        ----------
        series : str | None
            Raw series name.
        publisher_name : str | None
            Publisher name for filtering.

        Returns
        -------
        str | None
            Cleaned series name, or None if invalid or filtered out.
        """
        if not series:
            return None

        # Series must contain at least one character
        if not re.search(r"\S", series):
            return None

        # Remove sorting characters
        series = self.remove_sorting_characters(series) or ""
        if not series:
            return None

        # Skip series starting with publisher name
        if self._is_publisher_series(series, publisher_name):
            return None

        # Check against unwanted series patterns
        if self._matches_unwanted_pattern(series):
            return None

        return series.strip()

    def _is_publisher_series(self, series: str, publisher_name: str | None) -> bool:
        """Check if series name matches publisher name.

        Parameters
        ----------
        series : str
            Series name.
        publisher_name : str | None
            Publisher name.

        Returns
        -------
        bool
            True if series matches publisher name.
        """
        if not publisher_name:
            return False

        publisher_clean = self.remove_sorting_characters(publisher_name) or ""
        if not publisher_clean:
            return False

        if publisher_clean.lower() == series.lower():
            return True

        # Check if series starts with first 4+ characters of publisher
        match = re.search(r"^(\w{4,})", publisher_clean)
        if match:
            pub_prefix = match.group(1)
            return bool(
                re.search(
                    r"^\W*" + re.escape(pub_prefix),
                    series,
                    flags=re.IGNORECASE,
                ),
            )

        return False

    def _matches_unwanted_pattern(self, series: str) -> bool:
        """Check if series matches any unwanted pattern.

        Parameters
        ----------
        series : str
            Series name.

        Returns
        -------
        bool
            True if series matches unwanted pattern.
        """
        for pattern in self.UNWANTED_SERIES_PATTERNS:
            try:
                if re.search(pattern, series, flags=re.IGNORECASE):
                    return True
            except re.error:
                # Invalid regex pattern, skip
                continue
        return False
