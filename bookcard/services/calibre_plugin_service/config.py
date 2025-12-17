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

"""Calibre configuration path resolution."""

from __future__ import annotations

import os
from pathlib import Path


class CalibreConfigLocator:
    """Locate Calibre configuration paths.

    Parameters
    ----------
    config_dir : Path | None, optional
        Explicit Calibre config directory. If omitted, resolves from
        ``$CALIBRE_CONFIG_DIRECTORY`` then defaults to ``~/.config/calibre``.
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._explicit_config_dir = config_dir

    def get_config_dir(self) -> Path:
        """Return the Calibre configuration directory.

        Returns
        -------
        Path
            Calibre config directory.
        """
        if self._explicit_config_dir is not None:
            return self._explicit_config_dir
        env_dir = os.environ.get("CALIBRE_CONFIG_DIRECTORY")
        if env_dir:
            return Path(env_dir)
        return Path.home() / ".config" / "calibre"

    def get_plugins_dir(self) -> Path:
        """Return the directory containing user plugin ZIPs.

        Returns
        -------
        Path
            Calibre plugins directory.
        """
        return self.get_config_dir() / "plugins"

    def get_user_installed_plugin_names(self) -> set[str]:
        """Return plugin names installed by the user.

        Returns
        -------
        set[str]
            Plugin name stems from ``plugins/*.zip``.
        """
        plugins_dir = self.get_plugins_dir()
        if not plugins_dir.exists():
            return set()
        return {p.stem for p in plugins_dir.glob("*.zip")}
