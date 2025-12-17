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

"""Tests for EPUB fixer orchestrator."""

from bookcard.services.epub_fixer.core.epub import EPUBContents
from bookcard.services.epub_fixer.core.fixes.body_id_link import BodyIdLinkFix
from bookcard.services.epub_fixer.core.fixes.encoding import EncodingFix
from bookcard.services.epub_fixer.core.fixes.language import LanguageFix
from bookcard.services.epub_fixer.core.fixes.stray_img import StrayImageFix
from bookcard.services.epub_fixer.orchestrator import EPUBFixerOrchestrator


def test_orchestrator_init() -> None:
    """Test orchestrator initialization."""
    fixes = [EncodingFix(), LanguageFix()]
    orchestrator = EPUBFixerOrchestrator(fixes)

    assert len(orchestrator._fixes) == 2


def test_orchestrator_process_applies_all_fixes() -> None:
    """Test orchestrator applies all fixes."""
    fixes = [
        EncodingFix(),
        LanguageFix(default_language="en"),
        StrayImageFix(),
        BodyIdLinkFix(),
    ]
    orchestrator = EPUBFixerOrchestrator(fixes)

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
    <dc:title>Test Book</dc:title>
  </metadata>
</package>""",
            "chapter1.html": "<html><body><img /></body></html>",
        }
    )

    results = orchestrator.process(contents)

    # Should apply multiple fixes
    assert len(results) > 0


def test_orchestrator_process_empty_fixes() -> None:
    """Test orchestrator with empty fix list."""
    orchestrator = EPUBFixerOrchestrator([])

    contents = EPUBContents(files={"file.html": "<html></html>"})

    results = orchestrator.process(contents)

    assert len(results) == 0


def test_orchestrator_process_sequential() -> None:
    """Test orchestrator applies fixes sequentially."""
    # Create fixes that might interact
    fixes = [EncodingFix(), EncodingFix()]  # Same fix twice
    orchestrator = EPUBFixerOrchestrator(fixes)

    contents = EPUBContents(
        files={
            "chapter1.html": "<html><body>Content</body></html>",
        }
    )

    results = orchestrator.process(contents)

    # First fix should add encoding, second should see it exists
    assert len(results) >= 1


def test_orchestrator_process_modifies_contents() -> None:
    """Test orchestrator modifies contents in place."""
    fixes = [EncodingFix()]
    orchestrator = EPUBFixerOrchestrator(fixes)

    contents = EPUBContents(
        files={
            "chapter1.html": "<html><body>Content</body></html>",
        }
    )

    original_content = contents.files["chapter1.html"]
    orchestrator.process(contents)

    # Contents should be modified
    assert contents.files["chapter1.html"] != original_content
