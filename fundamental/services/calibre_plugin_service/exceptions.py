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

"""Domain exceptions for Calibre plugin management."""

from __future__ import annotations


class CalibreNotFoundError(RuntimeError):
    """Raised when Calibre executables are not available."""


class CalibreCommandError(RuntimeError):
    """Raised when a Calibre CLI command fails."""

    def __init__(self, operation: str, *, stderr: str = "", stdout: str = "") -> None:
        """Initialize the exception.

        Parameters
        ----------
        operation : str
            Human-readable operation name (e.g., "list plugins").
        stderr : str, optional
            Captured stderr content.
        stdout : str, optional
            Captured stdout content.
        """
        self.operation = operation
        self.stderr = stderr
        self.stdout = stdout
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        """Build a concise error message."""
        detail = (self.stderr or self.stdout or "").strip()
        if detail:
            return f"Failed to {self.operation}: {detail}"
        return f"Failed to {self.operation}."


class PluginSourceError(RuntimeError):
    """Raised when a plugin source cannot be fetched or validated."""
