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

"""High-level Calibre plugin orchestration service."""

from __future__ import annotations

import contextlib
import json
import subprocess  # noqa: S404
from dataclasses import dataclass
from typing import TYPE_CHECKING

from fundamental.services.calibre_plugin_service.commands import (
    CalibreCommandRunner,
    ExecutableLocator,
)
from fundamental.services.calibre_plugin_service.config import CalibreConfigLocator
from fundamental.services.calibre_plugin_service.exceptions import (
    CalibreCommandError,
    CalibreNotFoundError,
)
from fundamental.services.calibre_plugin_service.parsers import CompositeParser
from fundamental.services.calibre_plugin_service.parsers.legacy import (
    LegacyFormatParser,
)
from fundamental.services.calibre_plugin_service.parsers.table import TableFormatParser
from fundamental.services.calibre_plugin_service.scripts import (
    LIST_USER_PLUGINS_AS_JSON,
)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from fundamental.services.calibre_plugin_service.models import PluginInfo
    from fundamental.services.calibre_plugin_service.sources.base import PluginSource

_CALIBRE_NOT_FOUND_MSG = (
    "Calibre is not installed or not found in PATH. "
    "Please install Calibre to use plugin management features."
)


@contextlib.contextmanager
def _calibre_command_context(operation: str) -> Iterator[None]:
    """Normalize Calibre command failures into domain exceptions."""
    try:
        yield
    except FileNotFoundError as e:
        raise CalibreNotFoundError(_CALIBRE_NOT_FOUND_MSG) from e
    except subprocess.CalledProcessError as e:
        raise CalibreCommandError(
            operation,
            stderr=str(e.stderr or ""),
            stdout=str(e.stdout or ""),
        ) from e


@dataclass(slots=True)
class CalibrePluginService:
    """Orchestrate Calibre plugin operations.

    Parameters
    ----------
    config_locator : CalibreConfigLocator
        Calibre config path resolver.
    command_runner : CalibreCommandRunner
        Runner for Calibre CLI commands.
    executable_locator : ExecutableLocator
        Locator for optional executables (e.g., ``calibre-debug``).
    parser : CompositeParser
        Output parser for ``calibre-customize -l``.
    """

    config_locator: CalibreConfigLocator
    command_runner: CalibreCommandRunner
    executable_locator: ExecutableLocator
    parser: CompositeParser

    def list_plugins(self) -> list[PluginInfo]:
        """List installed plugins.

        Returns
        -------
        list[PluginInfo]
            Installed plugin info.

        Raises
        ------
        CalibreNotFoundError
            If Calibre is not available.
        CalibreCommandError
            If Calibre fails to list plugins.
        """
        if self.executable_locator.exists("calibre-debug"):
            try:
                return self._list_plugins_via_debug()
            except (CalibreNotFoundError, CalibreCommandError, ValueError, TypeError):
                # Optional path: fall back to scraping calibre-customize output.
                pass

        with _calibre_command_context("list plugins"):
            result = self.command_runner.customize("-l")

        return self.parser.parse(result.stdout or "")

    def install(self, source: PluginSource) -> None:
        """Install a plugin from a source.

        Parameters
        ----------
        source : PluginSource
            Source yielding a plugin ZIP.

        Raises
        ------
        CalibreNotFoundError
            If Calibre is not available.
        CalibreCommandError
            If Calibre fails to install the plugin.
        """
        with (
            source.open() as zip_path,
            _calibre_command_context("install plugin"),
        ):
            self.command_runner.customize("--add", str(zip_path))

    def remove(self, plugin_name: str) -> None:
        """Remove an installed plugin.

        Parameters
        ----------
        plugin_name : str
            Plugin name.

        Raises
        ------
        CalibreNotFoundError
            If Calibre is not available.
        CalibreCommandError
            If Calibre fails to remove the plugin.
        """
        with _calibre_command_context("remove plugin"):
            self.command_runner.customize("--remove-plugin", plugin_name)

    def _list_plugins_via_debug(self) -> list[PluginInfo]:
        """List user-installed plugins via ``calibre-debug`` JSON script."""
        with _calibre_command_context("list plugins"):
            result = self.command_runner.debug(LIST_USER_PLUGINS_AS_JSON)

        stdout = (result.stdout or "").strip()
        data = json.loads(stdout) if stdout else []
        if not isinstance(data, list):
            msg = "Unexpected calibre-debug output"
            raise TypeError(msg)

        plugins: list[PluginInfo] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            plugins.append({
                "name": str(item.get("name", "")),
                "version": str(item.get("version", "")),
                "author": str(item.get("author", "Unknown") or "Unknown"),
                "description": str(item.get("description", "")),
            })

        return plugins


def create_default_calibre_plugin_service() -> CalibrePluginService:
    """Create the default Calibre plugin service.

    Returns
    -------
    CalibrePluginService
        Service instance.
    """
    from fundamental.services.calibre_plugin_service.commands import (
        ShutilExecutableLocator,
        SubprocessExecutor,
    )

    executor = SubprocessExecutor()
    config_locator = CalibreConfigLocator()
    runner = CalibreCommandRunner(executor=executor)

    parser = CompositeParser(
        parsers=(
            TableFormatParser(config_locator.get_user_installed_plugin_names),
            LegacyFormatParser(),
        )
    )

    return CalibrePluginService(
        config_locator=config_locator,
        command_runner=runner,
        executable_locator=ShutilExecutableLocator(),
        parser=parser,
    )
