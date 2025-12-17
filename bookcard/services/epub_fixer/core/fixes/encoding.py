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

"""Encoding fix implementation.

Adds UTF-8 encoding declaration if missing from HTML/XHTML files.
"""

import re

from bookcard.models.epub_fixer import EPUBFixType
from bookcard.services.epub_fixer.core.epub import EPUBContents, FixResult
from bookcard.services.epub_fixer.core.fixes.base import EPUBFix
from bookcard.services.epub_fixer.utils.file_types import FileTypes


class EncodingFix(EPUBFix):
    """Fix for missing UTF-8 encoding declarations in HTML/XHTML files."""

    def __init__(self) -> None:
        """Initialize encoding fix."""
        self._encoding_declaration = '<?xml version="1.0" encoding="utf-8"?>'
        self._encoding_regex = r'^<\?xml\s+version=["\'][\d.]+["\']\s+encoding=["\'][a-zA-Z\d\-\.]+["\'].*?\?>'

    @property
    def fix_type(self) -> EPUBFixType:
        """Return fix type.

        Returns
        -------
        EPUBFixType
            ENCODING fix type.
        """
        return EPUBFixType.ENCODING

    def apply(self, contents: EPUBContents) -> list[FixResult]:
        """Add UTF-8 encoding declaration if missing.

        Parameters
        ----------
        contents : EPUBContents
            EPUB contents to fix (modified in place).

        Returns
        -------
        list[FixResult]
            List of fixes applied.
        """
        results: list[FixResult] = []

        for filename in list(contents.files.keys()):
            if not FileTypes.is_html_file(filename):
                continue

            html = contents.files[filename]
            html = html.lstrip()

            if not re.match(self._encoding_regex, html, re.IGNORECASE):
                html = self._encoding_declaration + "\n" + html
                contents.files[filename] = html
                results.append(
                    FixResult(
                        fix_type=self.fix_type,
                        description=f"Fixed encoding for file {filename}",
                        file_name=filename,
                    )
                )

        return results
