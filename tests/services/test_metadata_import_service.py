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

"""Tests for metadata import service to achieve 100% coverage."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fundamental.services.metadata_import_service import MetadataImportService


def test_init_default_importers() -> None:
    """Test __init__ with default importers."""
    service = MetadataImportService()
    assert len(service._importers) == 2


def test_init_custom_importers() -> None:
    """Test __init__ with custom importers."""
    mock_importer1 = MagicMock()
    mock_importer2 = MagicMock()
    service = MetadataImportService(importers=[mock_importer1, mock_importer2])

    assert len(service._importers) == 2
    assert service._importers[0] == mock_importer1
    assert service._importers[1] == mock_importer2


def test_import_metadata_opf() -> None:
    """Test import_metadata with OPF format."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
    </metadata>
</package>"""
    service = MetadataImportService()
    result = service.import_metadata(opf_content, "opf")

    assert result.title == "Test Book"


def test_import_metadata_yaml() -> None:
    """Test import_metadata with YAML format."""
    yaml_content = """title: Test Book
authors:
  - Author One
"""
    service = MetadataImportService()
    result = service.import_metadata(yaml_content, "yaml")

    assert result.title == "Test Book"
    assert result.author_names == ["Author One"]


def test_import_metadata_yml() -> None:
    """Test import_metadata with yml format."""
    yaml_content = """title: Test Book
"""
    service = MetadataImportService()
    result = service.import_metadata(yaml_content, "yml")

    assert result.title == "Test Book"


def test_import_metadata_case_insensitive() -> None:
    """Test import_metadata is case insensitive."""
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
    <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
        <dc:title>Test Book</dc:title>
    </metadata>
</package>"""
    service = MetadataImportService()
    result = service.import_metadata(opf_content, "OPF")

    assert result.title == "Test Book"


def test_import_metadata_unsupported_format() -> None:
    """Test import_metadata with unsupported format."""
    service = MetadataImportService()
    with pytest.raises(ValueError, match="Unsupported format"):
        service.import_metadata("content", "json")


def test_import_metadata_unsupported_format_dynamic_supported() -> None:
    """Test import_metadata shows dynamically determined supported formats."""
    mock_importer = MagicMock()
    mock_importer.can_handle.return_value = False
    service = MetadataImportService(importers=[mock_importer])

    with pytest.raises(ValueError, match="Unsupported format: json"):
        service.import_metadata("content", "json")


def test_import_metadata_uses_custom_importer() -> None:
    """Test import_metadata uses custom importer."""
    mock_importer = MagicMock()
    mock_importer.can_handle.return_value = True
    mock_result = MagicMock()
    mock_importer.import_metadata.return_value = mock_result

    service = MetadataImportService(importers=[mock_importer])
    result = service.import_metadata("content", "custom")

    mock_importer.can_handle.assert_called_once_with("custom")
    mock_importer.import_metadata.assert_called_once_with("content")
    assert result == mock_result
