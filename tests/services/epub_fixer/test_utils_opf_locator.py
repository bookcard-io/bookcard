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

"""Tests for OPF locator utility."""

from bookcard.services.epub_fixer.utils.opf_locator import OPFLocator


def test_find_opf_path_success() -> None:
    """Test finding OPF path from valid container.xml."""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
    }

    result = OPFLocator.find_opf_path(files)
    assert result == "content.opf"


def test_find_opf_path_multiple_rootfiles() -> None:
    """Test finding OPF path when multiple rootfiles exist."""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="other.opf" media-type="application/xml"/>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
    }

    result = OPFLocator.find_opf_path(files)
    assert result == "content.opf"


def test_find_opf_path_no_container() -> None:
    """Test finding OPF path when container.xml is missing."""
    files = {"other.xml": "<xml></xml>"}

    result = OPFLocator.find_opf_path(files)
    assert result is None


def test_find_opf_path_invalid_xml() -> None:
    """Test finding OPF path with invalid XML."""
    files = {
        "META-INF/container.xml": "not valid xml",
    }

    result = OPFLocator.find_opf_path(files)
    assert result is None


def test_find_opf_path_no_opf_rootfile() -> None:
    """Test finding OPF path when no OPF rootfile exists."""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="other.xml" media-type="application/xml"/>
  </rootfiles>
</container>""",
    }

    result = OPFLocator.find_opf_path(files)
    assert result is None


def test_find_opf_path_empty_container() -> None:
    """Test finding OPF path with empty container."""
    files = {
        "META-INF/container.xml": """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
  </rootfiles>
</container>""",
    }

    result = OPFLocator.find_opf_path(files)
    assert result is None
