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

"""Tests for local plugin source to achieve 100% coverage."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from bookcard.services.calibre_plugin_service.sources.local import LocalZipSource

if TYPE_CHECKING:
    from pathlib import Path


class TestLocalZipSource:
    """Test LocalZipSource class."""

    def test_open_success(self, tmp_path: Path) -> None:
        """Test open with valid ZIP file.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        zip_file = tmp_path / "plugin.zip"
        zip_file.write_bytes(b"PK\x03\x04fake zip content")

        source = LocalZipSource(path=zip_file)

        with source.open() as path:
            assert path == zip_file
            assert path.exists()

    def test_open_file_not_found(self, tmp_path: Path) -> None:
        """Test open with non-existent file.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        non_existent = tmp_path / "missing.zip"
        source = LocalZipSource(path=non_existent)

        with (
            pytest.raises(FileNotFoundError, match="Plugin file not found"),
            source.open(),
        ):
            pass

    @pytest.mark.parametrize(
        "suffix",
        [".txt", ".tar", ".gz"],
    )
    def test_open_not_zip(self, tmp_path: Path, suffix: str) -> None:
        """Test open with non-ZIP file extension.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        suffix : str
            File suffix to test.
        """
        file_path = tmp_path / f"plugin{suffix}"
        file_path.write_bytes(b"fake content")
        source = LocalZipSource(path=file_path)

        with (
            pytest.raises(ValueError, match=r"Only \.zip plugins are supported"),
            source.open(),
        ):
            pass

    def test_open_zip_case_insensitive(self, tmp_path: Path) -> None:
        """Test open accepts ZIP files with different case extensions.

        Parameters
        ----------
        tmp_path : Path
            Temporary directory path.
        """
        for suffix in [".zip", ".ZIP", ".Zip", ".zIp"]:
            zip_file = tmp_path / f"plugin{suffix}"
            zip_file.write_bytes(b"PK\x03\x04fake zip content")
            source = LocalZipSource(path=zip_file)

            with source.open() as path:
                assert path == zip_file
                assert path.exists()
