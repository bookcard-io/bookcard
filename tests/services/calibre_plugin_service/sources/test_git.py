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

"""Tests for git plugin source to achieve 100% coverage."""

from __future__ import annotations

import subprocess  # noqa: S404
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from bookcard.services.calibre_plugin_service.exceptions import PluginSourceError
from bookcard.services.calibre_plugin_service.sources.base import (
    DefaultTempDirectoryFactory,
)
from bookcard.services.calibre_plugin_service.sources.git import (
    GitRepositoryZipSource,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


class FakeExecutor:
    """Fake command executor for testing."""

    def __init__(self) -> None:
        """Initialize fake executor."""
        self.calls: list[list[str]] = []
        self._errors: dict[str, Exception] = {}

    def set_error(self, executable: str, error: Exception) -> None:
        """Set error to raise for executable.

        Parameters
        ----------
        executable : str
            Executable name.
        error : Exception
            Error to raise.
        """
        self._errors[executable] = error

    def run(
        self, args: Sequence[str], *, timeout_s: float
    ) -> subprocess.CompletedProcess[str]:
        """Run command.

        Parameters
        ----------
        args : list[str]
            Command arguments.
        timeout_s : float
            Timeout in seconds.

        Returns
        -------
        subprocess.CompletedProcess[str]
            Completed process result.

        Raises
        ------
        Exception
            If error was set for this executable.
        """
        self.calls.append(list(args))
        exe = args[0]
        if exe in self._errors:
            raise self._errors[exe]
        return subprocess.CompletedProcess(
            args=args, returncode=0, stdout="", stderr=""
        )


@pytest.fixture
def executor() -> FakeExecutor:
    """Create fake executor.

    Returns
    -------
    FakeExecutor
        Fake executor instance.
    """
    return FakeExecutor()


@pytest.fixture
def tempdirs() -> DefaultTempDirectoryFactory:
    """Create temp directory factory.

    Returns
    -------
    DefaultTempDirectoryFactory
        Temp directory factory instance.
    """
    return DefaultTempDirectoryFactory()


class TestGitRepositoryZipSource:
    """Test GitRepositoryZipSource class."""

    def test_open_success_no_branch(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open with successful clone, no branch.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            patch("shutil.make_archive") as mock_make_archive,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_make_archive.return_value = "/tmp/test.zip"
            with source.open() as zip_path:
                assert zip_path.suffix == ".zip"

        assert executor.calls
        assert "git" in executor.calls[0]
        assert "--branch" not in executor.calls[0]

    def test_open_success_with_branch(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open with successful clone, with branch.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch="main",
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            patch("shutil.make_archive") as mock_make_archive,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_make_archive.return_value = "/tmp/test.zip"
            with source.open() as zip_path:
                assert zip_path.suffix == ".zip"

        assert executor.calls
        assert "--branch" in executor.calls[0]
        assert "main" in executor.calls[0]

    def test_open_git_not_found(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when git is not found.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        executor.set_error("git", FileNotFoundError("git not found"))
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            pytest.raises(
                PluginSourceError, match="git is not installed or not found on PATH"
            ),
            source.open(),
        ):
            pass

    def test_open_clone_fails(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when git clone fails.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        error = subprocess.CalledProcessError(
            1, ["git", "clone"], stderr="Repository not found"
        )
        executor.set_error("git", error)
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            pytest.raises(PluginSourceError, match="Failed to clone repository"),
            source.open(),
        ):
            pass

    def test_open_plugin_path_not_found(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when plugin path doesn't exist in repo.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo="nonexistent/path",
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with patch("pathlib.Path.exists") as mock_exists:
            # First call for zip_path check, second for plugin_path_in_repo
            mock_exists.side_effect = [False, False]
            with (
                pytest.raises(
                    PluginSourceError,
                    match="Plugin path 'nonexistent/path' not found in repository",
                ),
                source.open(),
            ):
                pass

    def test_open_make_archive_fails(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when make_archive fails.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            patch("shutil.make_archive", side_effect=OSError("Permission denied")),
            pytest.raises(PluginSourceError, match="Failed to create plugin ZIP"),
            source.open(),
        ):
            pass

    def test_open_zip_not_created(
        self, executor: FakeExecutor, tempdirs: DefaultTempDirectoryFactory
    ) -> None:
        """Test open when ZIP file doesn't exist after creation.

        Parameters
        ----------
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url="https://github.com/user/repo.git",
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            patch("shutil.make_archive", return_value="/tmp/test.zip"),
            patch("pathlib.Path.exists", return_value=False),
            pytest.raises(PluginSourceError, match="Failed to create plugin ZIP"),
            source.open(),
        ):
            pass

    @pytest.mark.parametrize(
        "repo_url",
        [
            "git@github.com:user/repo.git",
            "git@gitlab.com:user/repo.git",
        ],
    )
    def test_validate_repo_url_git_at(
        self,
        repo_url: str,
        executor: FakeExecutor,
        tempdirs: DefaultTempDirectoryFactory,
    ) -> None:
        """Test validation accepts git@ URLs.

        Parameters
        ----------
        repo_url : str
            Git repository URL.
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url=repo_url,
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        # Should not raise
        with (
            patch("shutil.make_archive") as mock_make_archive,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_make_archive.return_value = "/tmp/test.zip"
            with source.open():
                pass

    @pytest.mark.parametrize(
        ("repo_url", "expected_error"),
        [
            (
                "invalid-url",
                "Invalid repo_url. Expected URL with scheme or git@host:path",
            ),
            (
                "ftp://example.com/repo.git",
                "Unsupported repo_url scheme: ftp",
            ),
            (
                "file:///path/to/repo.git",
                "Unsupported repo_url scheme: file",
            ),
        ],
    )
    def test_validate_repo_url_invalid(
        self,
        repo_url: str,
        expected_error: str,
        executor: FakeExecutor,
        tempdirs: DefaultTempDirectoryFactory,
    ) -> None:
        """Test validation rejects invalid URLs.

        Parameters
        ----------
        repo_url : str
            Invalid repository URL.
        expected_error : str
            Expected error message.
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url=repo_url,
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        with (
            pytest.raises(PluginSourceError, match=expected_error),
            source.open(),
        ):
            pass

    @pytest.mark.parametrize(
        "repo_url",
        [
            "https://github.com/user/repo.git",
            "http://github.com/user/repo.git",
            "ssh://git@github.com/user/repo.git",
            "git://github.com/user/repo.git",
        ],
    )
    def test_validate_repo_url_valid_schemes(
        self,
        repo_url: str,
        executor: FakeExecutor,
        tempdirs: DefaultTempDirectoryFactory,
    ) -> None:
        """Test validation accepts valid URL schemes.

        Parameters
        ----------
        repo_url : str
            Valid repository URL.
        executor : FakeExecutor
            Fake executor instance.
        tempdirs : DefaultTempDirectoryFactory
            Temp directory factory.
        """
        source = GitRepositoryZipSource(
            repo_url=repo_url,
            plugin_path_in_repo=None,
            branch=None,
            executor=executor,
            tempdirs=tempdirs,
            timeout_s=1.0,
        )

        # Should not raise
        with (
            patch("shutil.make_archive") as mock_make_archive,
            patch("pathlib.Path.exists", return_value=True),
        ):
            mock_make_archive.return_value = "/tmp/test.zip"
            with source.open():
                pass
