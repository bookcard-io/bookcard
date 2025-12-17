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

"""Git repository plugin source."""

from __future__ import annotations

import contextlib
import shutil
import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from bookcard.services.calibre_plugin_service.exceptions import PluginSourceError

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from bookcard.services.calibre_plugin_service.commands import CommandExecutor
    from bookcard.services.calibre_plugin_service.sources.base import (
        TempDirectoryFactory,
    )


def _validate_repo_url(repo_url: str) -> None:
    """Validate a Git repository URL."""
    if repo_url.startswith("git@"):  # scp-like ssh
        return
    if "://" not in repo_url:
        msg = "Invalid repo_url. Expected URL with scheme or git@host:path"
        raise PluginSourceError(msg)

    parsed = urlparse(repo_url)
    if parsed.scheme not in {"http", "https", "ssh", "git"}:
        msg = f"Unsupported repo_url scheme: {parsed.scheme}"
        raise PluginSourceError(msg)


@dataclass(frozen=True, slots=True)
class GitRepositoryZipSource:
    """Fetch a plugin by cloning a Git repository and zipping a directory.

    Parameters
    ----------
    repo_url : str
        Repository URL.
    plugin_path_in_repo : str | None, optional
        Subpath inside the repo to zip. If omitted, zips the repository root.
    branch : str | None, optional
        Branch/tag/commit.
    executor : CommandExecutor
        Command executor.
    tempdirs : TempDirectoryFactory
        Temporary directory factory.
    timeout_s : float, optional
        Timeout for git operations.
    """

    repo_url: str
    plugin_path_in_repo: str | None
    branch: str | None
    executor: CommandExecutor
    tempdirs: TempDirectoryFactory
    timeout_s: float = 120.0

    def open(self) -> contextlib.AbstractContextManager[Path]:
        """Clone repo and yield a generated ZIP path."""
        _validate_repo_url(self.repo_url)

        @contextlib.contextmanager
        def _cm() -> Iterator[Path]:
            with self.tempdirs.create(prefix="calibre_plugin_git_") as tmp:
                repo_dir = tmp / "repo"
                cmd = ["git", "clone", "--depth", "1"]
                if self.branch:
                    cmd.extend(["--branch", self.branch])
                cmd.extend([self.repo_url, str(repo_dir)])

                try:
                    self.executor.run(cmd, timeout_s=self.timeout_s)
                except FileNotFoundError as e:
                    msg = "git is not installed or not found on PATH"
                    raise PluginSourceError(msg) from e
                except subprocess.CalledProcessError as e:
                    detail = (e.stderr or "").strip()
                    msg = f"Failed to clone repository: {detail}"
                    raise PluginSourceError(msg) from e

                target_dir = repo_dir
                if self.plugin_path_in_repo:
                    target_dir = repo_dir / self.plugin_path_in_repo
                    if not target_dir.exists():
                        msg = f"Plugin path '{self.plugin_path_in_repo}' not found in repository"
                        raise PluginSourceError(msg)

                archive_base = tmp / "plugin"
                try:
                    shutil.make_archive(str(archive_base), "zip", root_dir=target_dir)
                except OSError as e:
                    msg = f"Failed to create plugin ZIP: {e}"
                    raise PluginSourceError(msg) from e

                zip_path = archive_base.with_suffix(".zip")
                if not zip_path.exists():
                    msg = "Failed to create plugin ZIP"
                    raise PluginSourceError(msg)

                yield zip_path

        return _cm()
