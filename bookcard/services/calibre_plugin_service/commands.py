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

"""Command execution primitives (IoC-friendly)."""

from __future__ import annotations

import shutil
import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence


class CommandExecutor(Protocol):
    """Execute external commands."""

    def run(
        self, args: Sequence[str], *, timeout_s: float
    ) -> subprocess.CompletedProcess[str]:
        """Run a command.

        Parameters
        ----------
        args : Sequence[str]
            Command + arguments.
        timeout_s : float
            Timeout in seconds.

        Returns
        -------
        subprocess.CompletedProcess[str]
            Completed process.
        """


class ExecutableLocator(Protocol):
    """Locate executables on PATH."""

    def exists(self, executable: str) -> bool:
        """Return True if executable exists on PATH."""


@dataclass(frozen=True, slots=True)
class SubprocessExecutor:
    """Default command executor based on ``subprocess.run``."""

    def run(
        self, args: Sequence[str], *, timeout_s: float
    ) -> subprocess.CompletedProcess[str]:
        """Run a command via ``subprocess.run``.

        Parameters
        ----------
        args : Sequence[str]
            Command + arguments.
        timeout_s : float
            Timeout in seconds.

        Returns
        -------
        subprocess.CompletedProcess[str]
            Completed process.
        """
        return subprocess.run(  # noqa: S603
            list(args),
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout_s,
        )


@dataclass(frozen=True, slots=True)
class ShutilExecutableLocator:
    """Default executable locator based on ``shutil.which``."""

    def exists(self, executable: str) -> bool:
        """Return True if executable exists on PATH.

        Parameters
        ----------
        executable : str
            Executable name.

        Returns
        -------
        bool
            True if executable is found on PATH.
        """
        return shutil.which(executable) is not None


@dataclass(frozen=True, slots=True)
class CalibreCommandRunner:
    """Run Calibre CLI commands.

    Parameters
    ----------
    executor : CommandExecutor
        Command executor.
    timeout_s : float, optional
        Timeout for Calibre commands.
    """

    executor: CommandExecutor
    timeout_s: float = 60.0

    def customize(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run ``calibre-customize``.

        Parameters
        ----------
        *args : str
            Arguments passed to ``calibre-customize``.

        Returns
        -------
        subprocess.CompletedProcess[str]
            Completed process.
        """
        return self.executor.run(["calibre-customize", *args], timeout_s=self.timeout_s)

    def debug(self, code: str) -> subprocess.CompletedProcess[str]:
        """Run ``calibre-debug -c <code>``.

        Parameters
        ----------
        code : str
            Python code executed by Calibre.

        Returns
        -------
        subprocess.CompletedProcess[str]
            Completed process.
        """
        return self.executor.run(
            ["calibre-debug", "-c", code], timeout_s=self.timeout_s
        )
