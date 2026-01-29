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

"""RAR/CBR extraction helpers.

This module exists because Python's `rarfile` library relies on external tools
to extract RAR members, and certain tool backends can be unreliable or buggy
depending on the environment.

We keep the logic here small and focused so archive handlers and cover
extractors can share the same behavior.
"""

from __future__ import annotations

import subprocess  # noqa: S404
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def extract_member_with_bsdtar(file_path: Path, *, filename: str) -> bytes:
    """Extract a single member from a RAR/CBR using `bsdtar`.

    Parameters
    ----------
    file_path : Path
        Path to the RAR/CBR archive.
    filename : str
        Member filename inside the archive.

    Returns
    -------
    bytes
        Extracted member bytes.

    Raises
    ------
    FileNotFoundError
        If `bsdtar` is not installed or not found on PATH.
    subprocess.CalledProcessError
        If `bsdtar` fails to extract the member.
    OSError
        If process execution fails for OS reasons.
    """
    # NOTE: Avoid `--to-stdout` + `rarfile`'s tool wrapper; call bsdtar directly
    # with a stable invocation:
    #   bsdtar -x -O -f <archive> <member>
    #
    # (We intentionally do not inject `--` here; members are treated as operands
    # after option parsing, and our archive entry validation rejects traversal.)
    proc = subprocess.run(  # noqa: S603
        ["bsdtar", "-x", "-O", "-f", str(file_path), filename],  # noqa: S607
        check=True,
        capture_output=True,
    )
    return proc.stdout
