#!/usr/bin/env python3
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

"""Tests for the Calibre plugin service package."""

from __future__ import annotations

import subprocess  # noqa: S404
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from bookcard.services.calibre_plugin_service import (
    CalibreNotFoundError,
    CalibrePluginService,
)
from bookcard.services.calibre_plugin_service.commands import CalibreCommandRunner
from bookcard.services.calibre_plugin_service.config import CalibreConfigLocator
from bookcard.services.calibre_plugin_service.parsers import CompositeParser
from bookcard.services.calibre_plugin_service.parsers.legacy import (
    LegacyFormatParser,
)
from bookcard.services.calibre_plugin_service.parsers.table import TableFormatParser
from bookcard.services.calibre_plugin_service.sources import (
    DefaultTempDirectoryFactory,
    GitRepositoryZipSource,
    LocalZipSource,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


@dataclass(frozen=True, slots=True)
class FakeLocator:
    """Fake executable locator."""

    debug_exists: bool = False

    def exists(self, executable: str) -> bool:
        return self.debug_exists if executable == "calibre-debug" else False


class FakeExecutor:
    """Fake command executor that routes outputs by argv[0]."""

    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self._responses: dict[str, subprocess.CompletedProcess[str]] = {}
        self._errors: dict[str, Exception] = {}

    def set_response(
        self, executable: str, *, stdout: str = "", stderr: str = ""
    ) -> None:
        self._responses[executable] = subprocess.CompletedProcess(
            args=[executable],
            returncode=0,
            stdout=stdout,
            stderr=stderr,
        )

    def set_error(self, executable: str, error: Exception) -> None:
        self._errors[executable] = error

    def run(
        self, args: Sequence[str], *, timeout_s: float
    ) -> subprocess.CompletedProcess[str]:
        argv = list(args)
        self.calls.append(argv)
        exe = argv[0]
        if exe in self._errors:
            raise self._errors[exe]
        return self._responses.get(exe) or subprocess.CompletedProcess(
            args=argv,
            returncode=0,
            stdout="",
            stderr="",
        )


@pytest.fixture
def service(tmp_path: Path) -> CalibrePluginService:
    """Create a service with fake dependencies."""
    config = CalibreConfigLocator(config_dir=tmp_path)
    executor = FakeExecutor()
    runner = CalibreCommandRunner(executor=executor, timeout_s=1.0)
    parser = CompositeParser(
        parsers=(
            TableFormatParser(config.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    return CalibrePluginService(
        config_locator=config,
        command_runner=runner,
        executable_locator=FakeLocator(debug_exists=False),
        parser=parser,
    )


def test_list_plugins_parses_table_and_filters_user_plugins(
    tmp_path: Path,
) -> None:
    """Table parser should filter to plugins/*.zip names."""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir(parents=True)
    (plugins_dir / "DeDRM.zip").write_bytes(b"")

    output = """Type                  Name                                                  Version        Disabled

File type             DeDRM                                                 (10, 0, 9)     False
  Removes DRM from books. Credit given to i♥cabbages and The Dark Reverser for the original scripts.

File type             HTML to ZIP                                           (8, 15, 0)     False
  Follow all local links.
"""

    executor = FakeExecutor()
    executor.set_response("calibre-customize", stdout=output)

    config = CalibreConfigLocator(config_dir=tmp_path)
    runner = CalibreCommandRunner(executor=executor, timeout_s=1.0)
    parser = CompositeParser(
        parsers=(
            TableFormatParser(config.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    svc = CalibrePluginService(
        config_locator=config,
        command_runner=runner,
        executable_locator=FakeLocator(debug_exists=False),
        parser=parser,
    )

    plugins = svc.list_plugins()

    assert [p["name"] for p in plugins] == ["DeDRM"]
    assert plugins[0]["version"] == "10, 0, 9"
    assert plugins[0]["author"] == "i♥cabbages and The Dark Reverser"


def test_list_plugins_falls_back_from_debug_to_customize(tmp_path: Path) -> None:
    """If calibre-debug fails, we fall back to calibre-customize."""
    executor = FakeExecutor()
    executor.set_error(
        "calibre-debug",
        subprocess.CalledProcessError(1, ["calibre-debug"], stderr="boom"),
    )
    executor.set_response(
        "calibre-customize", stdout="Plugin (1.0.0) by author\n  Desc"
    )

    config = CalibreConfigLocator(config_dir=tmp_path)
    runner = CalibreCommandRunner(executor=executor, timeout_s=1.0)
    parser = CompositeParser(
        parsers=(
            TableFormatParser(config.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    svc = CalibrePluginService(
        config_locator=config,
        command_runner=runner,
        executable_locator=FakeLocator(debug_exists=True),
        parser=parser,
    )

    plugins = svc.list_plugins()
    assert len(plugins) == 1
    assert plugins[0]["name"] == "Plugin"


def test_install_local_source_runs_calibre_customize_add(tmp_path: Path) -> None:
    """Local zip install should call calibre-customize --add."""
    zip_path = tmp_path / "plugin.zip"
    zip_path.write_bytes(b"PK\x03\x04fake")

    executor = FakeExecutor()
    executor.set_response("calibre-customize", stdout="")

    config = CalibreConfigLocator(config_dir=tmp_path)
    runner = CalibreCommandRunner(executor=executor, timeout_s=1.0)
    parser = CompositeParser(
        parsers=(
            TableFormatParser(config.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    svc = CalibrePluginService(
        config_locator=config,
        command_runner=runner,
        executable_locator=FakeLocator(debug_exists=False),
        parser=parser,
    )

    svc.install(LocalZipSource(zip_path))

    assert executor.calls[0][:2] == ["calibre-customize", "--add"]
    assert executor.calls[0][2] == str(zip_path)


def test_remove_missing_calibre_raises_calibre_not_found(tmp_path: Path) -> None:
    """FileNotFoundError from runner should become CalibreNotFoundError."""
    executor = FakeExecutor()
    executor.set_error("calibre-customize", FileNotFoundError("nope"))

    config = CalibreConfigLocator(config_dir=tmp_path)
    runner = CalibreCommandRunner(executor=executor, timeout_s=1.0)
    parser = CompositeParser(
        parsers=(
            TableFormatParser(config.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    svc = CalibrePluginService(
        config_locator=config,
        command_runner=runner,
        executable_locator=FakeLocator(debug_exists=False),
        parser=parser,
    )

    with pytest.raises(CalibreNotFoundError):
        svc.remove("DeDRM")


def test_git_source_clones_and_zips(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Git repository source should invoke git clone and create a zip path."""

    # Arrange fake executor to "succeed" git clone.
    executor = FakeExecutor()
    executor.set_response("git", stdout="")

    # Patch make_archive to create the expected zip file.
    def _fake_make_archive(base_name: str, fmt: str, *, root_dir: Path) -> str:
        zip_path = Path(base_name).with_suffix(".zip")
        zip_path.write_bytes(b"PK\x03\x04fake")
        return str(zip_path)

    monkeypatch.setattr("shutil.make_archive", _fake_make_archive)

    # The source will create tmp/ repo_dir; we just need it to exist.
    tempdirs = DefaultTempDirectoryFactory()

    source = GitRepositoryZipSource(
        repo_url="https://github.com/user/repo.git",
        plugin_path_in_repo=None,
        branch=None,
        executor=executor,
        tempdirs=tempdirs,
        timeout_s=1.0,
    )

    with source.open() as zip_path:
        assert zip_path.suffix == ".zip"
        assert zip_path.exists()

    assert executor.calls
    assert executor.calls[0][0] == "git"
