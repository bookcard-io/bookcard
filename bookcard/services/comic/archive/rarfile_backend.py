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

"""Helpers for configuring `rarfile` extraction backends.

`rarfile` can use multiple external tools for extraction (unrar/unar/7z/bsdtar).
In some environments (notably Linux + RAR5), `unar` may succeed partially and
then EOF, causing `rarfile` to raise `BadRarFile` for an otherwise valid archive.

We prefer `bsdtar` (libarchive) on Linux when available, as it has proven to be
more reliable for the problematic CBRs we ingest.
"""

import shutil
from types import ModuleType

from bookcard.constants import IS_LINUX


def prefer_bsdtar_on_linux(rarfile_module: ModuleType) -> None:
    """Prefer `bsdtar` backend for `rarfile` extraction on Linux.

    Parameters
    ----------
    rarfile_module : module
        The imported `rarfile` module.

    Notes
    -----
    `rarfile` selects a tool using a fixed preference order:

    - `unrar` (if present)
    - `unar`
    - `7z` / `7zz`
    - `bsdtar`

    We have observed RAR5 CBRs where `unar` returns a truncated stream and
    `7z` fails with "Unsupported Method", while `bsdtar -xf` succeeds.

    This function forces `rarfile` to skip `unar`/`7z` and use `bsdtar` when
    available. If `unrar` is present, it will still be preferred.
    """
    if not IS_LINUX:
        return

    # Only attempt this override when bsdtar exists on PATH.
    if shutil.which("bsdtar") is None:
        return

    tool_setup = getattr(rarfile_module, "tool_setup", None)
    if tool_setup is None:
        return

    # Prefer unrar if available; otherwise bsdtar. Avoid unar/7z which can fail
    # on some RAR5 compression methods.
    rar_cannot_exec = getattr(rarfile_module, "RarCannotExec", None)
    expected_errors: tuple[type[BaseException], ...] = (OSError, ValueError, TypeError)
    if isinstance(rar_cannot_exec, type) and issubclass(rar_cannot_exec, Exception):
        expected_errors = (*expected_errors, rar_cannot_exec)
    try:
        tool_setup(
            unrar=True,
            unar=False,
            bsdtar=True,
            sevenzip=False,
            sevenzip2=False,
            force=True,
        )
    except expected_errors:
        # If rarfile rejects the configuration for any reason, keep defaults.
        # We intentionally do not fail extraction here; the actual read will
        # surface a concrete error if no working tool exists.
        return
