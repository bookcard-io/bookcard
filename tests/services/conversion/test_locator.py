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

"""Tests for ConverterLocator to achieve 100% coverage."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from bookcard.services.conversion.locator import ConverterLocator


@pytest.fixture
def locator() -> ConverterLocator:
    """Create ConverterLocator instance.

    Returns
    -------
    ConverterLocator
        Locator instance.
    """
    return ConverterLocator()


@pytest.mark.parametrize(
    ("docker_exists", "which_result", "expected_path"),
    [
        (True, None, Path("/app/calibre/ebook-convert")),
        (False, "/usr/bin/ebook-convert", Path("/usr/bin/ebook-convert")),
        (False, None, None),
    ],
)
def test_find_converter(
    locator: ConverterLocator,
    docker_exists: bool,
    which_result: str | None,
    expected_path: Path | None,
) -> None:
    """Test find_converter with different scenarios.

    Parameters
    ----------
    locator : ConverterLocator
        Locator fixture.
    docker_exists : bool
        Whether Docker path exists.
    which_result : str | None
        Result from shutil.which.
    expected_path : Path | None
        Expected converter path.
    """
    docker_path_str = "/app/calibre/ebook-convert"

    def exists_new(self: Path) -> bool:
        if self.as_posix() == docker_path_str:
            return docker_exists
        return False

    with (
        patch.object(Path, "exists", new=exists_new),
        patch("shutil.which", return_value=which_result),
    ):
        result = locator.find_converter()

    assert result == expected_path


def test_find_converter_docker_path_first(
    locator: ConverterLocator,
) -> None:
    """Test find_converter prioritizes Docker path.

    Parameters
    ----------
    locator : ConverterLocator
        Locator fixture.
    """
    docker_path_str = "/app/calibre/ebook-convert"

    def exists_new(self: Path) -> bool:
        return self.as_posix() == docker_path_str

    with (
        patch.object(Path, "exists", new=exists_new),
        patch(
            "shutil.which",
            return_value="/usr/bin/ebook-convert",
        ) as mock_which,
    ):
        result = locator.find_converter()

    assert result == Path("/app/calibre/ebook-convert")
    # shutil.which should not be called if Docker path exists
    mock_which.assert_not_called()


def test_find_converter_falls_back_to_path(
    locator: ConverterLocator,
) -> None:
    """Test find_converter falls back to PATH lookup.

    Parameters
    ----------
    locator : ConverterLocator
        Locator fixture.
    """
    docker_path_str = "/app/calibre/ebook-convert"
    path_result = "/usr/local/bin/ebook-convert"

    def exists_new(self: Path) -> bool:
        if self.as_posix() == docker_path_str:
            return False
        return False

    with (
        patch.object(Path, "exists", new=exists_new),
        patch(
            "shutil.which",
            return_value=path_result,
        ) as mock_which,
    ):
        result = locator.find_converter()

    assert result == Path(path_result)
    mock_which.assert_called_once_with("ebook-convert")


def test_find_converter_returns_none_when_not_found(
    locator: ConverterLocator,
) -> None:
    """Test find_converter returns None when converter not found.

    Parameters
    ----------
    locator : ConverterLocator
        Locator fixture.
    """
    docker_path_str = "/app/calibre/ebook-convert"

    def exists_new(self: Path) -> bool:
        if self.as_posix() == docker_path_str:
            return False
        return False

    with (
        patch.object(Path, "exists", new=exists_new),
        patch(
            "shutil.which",
            return_value=None,
        ),
    ):
        result = locator.find_converter()

    assert result is None
