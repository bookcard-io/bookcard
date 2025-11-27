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

"""Body ID link fix implementation.

Fixes linking to body ID showing up as unresolved hyperlink.
"""

from contextlib import suppress
from pathlib import Path
from xml.parsers.expat import ExpatError

from defusedxml import minidom

from fundamental.models.epub_fixer import EPUBFixType
from fundamental.services.epub_fixer.core.epub import EPUBContents, FixResult
from fundamental.services.epub_fixer.core.fixes.base import EPUBFix
from fundamental.services.epub_fixer.utils.file_types import FileTypes


class BodyIdLinkFix(EPUBFix):
    """Fix for body ID hyperlink issues."""

    @property
    def fix_type(self) -> EPUBFixType:
        """Return fix type.

        Returns
        -------
        EPUBFixType
            BODY_ID_LINK fix type.
        """
        return EPUBFixType.BODY_ID_LINK

    def apply(self, contents: EPUBContents) -> list[FixResult]:
        """Fix linking to body ID showing up as unresolved hyperlink.

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
        body_id_list: list[tuple[str, str]] = []

        # Create list of ID tag of <body>
        for filename in contents.files:
            if not FileTypes.is_html_file(filename):
                continue

            with suppress(ExpatError, ValueError):
                html = contents.files[filename]
                dom = minidom.parseString(html)
                body_elements = dom.getElementsByTagName("body")

                if body_elements and body_elements[0].hasAttribute("id"):
                    body_id = body_elements[0].getAttribute("id")
                    if body_id:
                        filename_base = Path(filename).name
                        link_target = f"{filename_base}#{body_id}"
                        body_id_list.append((link_target, filename_base))

        # Replace all occurrences
        for filename in contents.files:
            for src, target in body_id_list:
                if src in contents.files[filename]:
                    contents.files[filename] = contents.files[filename].replace(
                        src, target
                    )
                    results.append(
                        FixResult(
                            fix_type=self.fix_type,
                            description=f"Replaced link target {src} with {target} in file {filename}",
                            file_name=filename,
                        )
                    )

        return results
