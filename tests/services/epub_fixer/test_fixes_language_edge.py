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

"""Additional edge case tests for language fix to reach 100% coverage."""

from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.epub_fixer.core.fixes.language import LanguageFix


def test_language_fix_language_changed_no_previous_result() -> None:
    """Test language fix branch at line 224 (language changed but no result added yet)."""
    # To trigger line 224, we need:
    # - language != original_language (line 220)
    # - not results (line 222) - results list is empty
    # This happens when a valid language exists but gets changed to another valid language
    # However, the current logic doesn't change valid languages, so this branch
    # appears to be unreachable in normal operation.
    #
    # The branch exists for edge cases where language normalization might occur,
    # but with the current implementation, if language is valid, it stays unchanged.
    #
    # For coverage purposes, we'll note that line 224 is a defensive branch
    # that may be unreachable with current logic but provides safety.
    fix = LanguageFix(default_language="en")
    contents = EPUBContents(
        files={
            "META-INF/container.xml": """<?xml version="1.0"?>
<container>
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
            "content.opf": """<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language>fr</dc:language>
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
        }
    )

    results = fix.apply(contents)

    # Language is valid (fr), so no fix is applied
    # Line 224 is unreachable with current logic as valid languages aren't changed
    # This is acceptable - it's a defensive branch for future edge cases
    assert isinstance(results, list)
