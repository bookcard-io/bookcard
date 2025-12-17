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

"""Plugin source abstractions."""

from __future__ import annotations

import contextlib
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Iterator


class PluginSource(Protocol):
    """A source that yields a plugin ZIP path."""

    def open(self) -> contextlib.AbstractContextManager[Path]:
        """Open the source and yield a ZIP file path."""


class TempDirectoryFactory(Protocol):
    """Create temporary directories."""

    def create(self, *, prefix: str) -> contextlib.AbstractContextManager[Path]:
        """Create a temporary directory context manager."""


class DefaultTempDirectoryFactory:
    """Default temp dir factory using ``tempfile.TemporaryDirectory``."""

    def create(self, *, prefix: str) -> contextlib.AbstractContextManager[Path]:
        """Create a temporary directory context manager.

        Parameters
        ----------
        prefix : str
            Temporary directory name prefix.

        Returns
        -------
        contextlib.AbstractContextManager[Path]
            Context manager yielding the directory path.
        """

        @contextlib.contextmanager
        def _cm() -> Iterator[Path]:
            with tempfile.TemporaryDirectory(prefix=prefix) as d:
                yield Path(d)

        return _cm()
