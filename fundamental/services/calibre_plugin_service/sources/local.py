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

"""Local filesystem plugin source."""

from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class LocalZipSource:
    """Use an existing local ZIP file as plugin source."""

    path: Path

    def open(self) -> contextlib.AbstractContextManager[Path]:
        """Yield the ZIP path.

        Returns
        -------
        contextlib.AbstractContextManager[Path]
            Context manager yielding the ZIP path.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        ValueError
            If the file is not a ``.zip``.
        """
        if not self.path.exists():
            msg = f"Plugin file not found: {self.path}"
            raise FileNotFoundError(msg)
        if self.path.suffix.lower() != ".zip":
            msg = "Only .zip plugins are supported"
            raise ValueError(msg)

        @contextlib.contextmanager
        def _cm() -> Iterator[Path]:
            yield self.path

        return _cm()
