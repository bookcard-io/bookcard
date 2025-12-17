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

"""Stray image tag fix implementation.

Removes image tags with no source attribute.
"""

from contextlib import suppress
from xml.parsers.expat import ExpatError

from defusedxml import minidom

from bookcard.models.epub_fixer import EPUBFixType
from bookcard.services.epub_fixer.core.epub import EPUBContents, FixResult
from bookcard.services.epub_fixer.core.fixes.base import EPUBFix
from bookcard.services.epub_fixer.utils.file_types import FileTypes


class StrayImageFix(EPUBFix):
    """Fix for stray image tags with no source attribute."""

    @property
    def fix_type(self) -> EPUBFixType:
        """Return fix type.

        Returns
        -------
        EPUBFixType
            STRAY_IMG fix type.
        """
        return EPUBFixType.STRAY_IMG

    def apply(self, contents: EPUBContents) -> list[FixResult]:
        """Remove stray image tags with no source attribute.

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

            with suppress(ExpatError, ValueError):
                dom = minidom.parseString(contents.files[filename])
                stray_img = [
                    img
                    for img in dom.getElementsByTagName("img")
                    if not img.getAttribute("src")
                ]

                if stray_img:
                    for img in stray_img:
                        img.parentNode.removeChild(img)
                    contents.files[filename] = dom.toxml()
                    results.append(
                        FixResult(
                            fix_type=self.fix_type,
                            description=f"Removed stray image tag(s) in {filename}",
                            file_name=filename,
                        )
                    )

        return results
