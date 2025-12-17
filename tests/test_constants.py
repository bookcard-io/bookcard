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

"""Tests for application constants."""

import sys
from unittest.mock import patch

import pytest

from bookcard.constants import IS_HAIKU, IS_LINUX, IS_MACOS, IS_WIN


@pytest.mark.parametrize(
    ("platform", "expected_win", "expected_linux", "expected_macos", "expected_haiku"),
    [
        ("win32", True, False, False, False),
        ("linux", False, True, False, False),
        ("darwin", False, False, True, False),
        ("haiku1", False, False, False, True),
        ("freebsd", False, False, False, False),
    ],
)
def test_platform_constants(
    platform: str,
    expected_win: bool,
    expected_linux: bool,
    expected_macos: bool,
    expected_haiku: bool,
) -> None:
    """Test platform constant values based on sys.platform.

    Parameters
    ----------
    platform : str
        Platform identifier to test.
    expected_win : bool
        Expected value for IS_WIN.
    expected_linux : bool
        Expected value for IS_LINUX.
    expected_macos : bool
        Expected value for IS_MACOS.
    expected_haiku : bool
        Expected value for IS_HAIKU.
    """
    with patch.object(sys, "platform", platform):
        # Re-import to get updated constants
        import importlib

        import bookcard.constants as constants_module

        importlib.reload(constants_module)

        assert expected_win == constants_module.IS_WIN
        assert expected_linux == constants_module.IS_LINUX
        assert expected_macos == constants_module.IS_MACOS
        assert expected_haiku == constants_module.IS_HAIKU


def test_constants_import() -> None:
    """Test that constants can be imported and have boolean values."""
    assert isinstance(IS_WIN, bool)
    assert isinstance(IS_LINUX, bool)
    assert isinstance(IS_MACOS, bool)
    assert isinstance(IS_HAIKU, bool)
