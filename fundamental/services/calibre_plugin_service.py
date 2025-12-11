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

"""Calibre Plugin Service.

This service manages Calibre plugins (listing, installing, removing).
It acts as a wrapper around the `calibre-customize` CLI tool.
"""

import logging
import subprocess  # noqa: S404
from pathlib import Path
from typing import TypedDict

logger = logging.getLogger(__name__)


class PluginInfo(TypedDict):
    """Information about an installed plugin."""

    name: str
    version: str
    description: str
    author: str


class CalibrePluginService:
    """Service for managing Calibre plugins."""

    def list_plugins(self) -> list[PluginInfo]:
        """List installed Calibre plugins.

        Returns
        -------
        list[PluginInfo]
            List of installed plugins with details.
        """
        try:
            # calibre-customize -l returns list of plugins
            # Format is typically:
            # Plugin Name (Version) by Author
            #   Description...
            #
            # But parsing it might be tricky as it's designed for humans.
            # Example output:
            # DeDRM (7.2.1) by apprenticeharper
            #  Removes DRM from books.
            #
            # KoboTouchExtended (3.6.3) by jgoguen
            #  Extended driver for Kobo Touch/Glo/Mini/Aura/AuraHD/H2O/GloHD

            result = subprocess.run(
                ["calibre-customize", "-l"],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )

            return self._parse_plugin_list(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to list plugins: %s", e.stderr)
            msg = f"Failed to list plugins: {e.stderr}"
            raise RuntimeError(msg) from e

    def install_plugin(self, plugin_path: Path) -> None:
        """Install a plugin from a ZIP file.

        Parameters
        ----------
        plugin_path : Path
            Path to the plugin ZIP file.

        Raises
        ------
        RuntimeError
            If installation fails.
        """
        if not plugin_path.exists():
            msg = f"Plugin file not found: {plugin_path}"
            raise FileNotFoundError(msg)

        try:
            logger.info("Installing plugin from %s", plugin_path)
            subprocess.run(  # noqa: S603
                ["calibre-customize", "--add", str(plugin_path)],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Successfully installed plugin")
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to install plugin: %s", e.stderr)
            msg = f"Failed to install plugin: {e.stderr}"
            raise RuntimeError(msg) from e

    def remove_plugin(self, plugin_name: str) -> None:
        """Remove an installed plugin.

        Parameters
        ----------
        plugin_name : str
            Name of the plugin to remove.

        Raises
        ------
        RuntimeError
            If removal fails.
        """
        try:
            logger.info("Removing plugin: %s", plugin_name)
            subprocess.run(  # noqa: S603
                ["calibre-customize", "--remove-plugin", plugin_name],  # noqa: S607
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("Successfully removed plugin")
        except subprocess.CalledProcessError as e:
            logger.exception("Failed to remove plugin: %s", e.stderr)
            msg = f"Failed to remove plugin: {e.stderr}"
            raise RuntimeError(msg) from e

    def install_plugin_from_git(
        self,
        repo_url: str,
        plugin_path_in_repo: str | None = None,
        branch: str | None = None,
    ) -> None:
        """Install a plugin from a Git repository.

        Parameters
        ----------
        repo_url : str
            URL of the Git repository.
        plugin_path_in_repo : str | None
            Subdirectory containing the plugin code (e.g., 'DeDRM_plugin').
            If None, assumes root of repo or tries to auto-detect.
        branch : str | None
            Git branch/tag/commit to checkout.

        Raises
        ------
        RuntimeError
            If installation fails.
        """
        import shutil
        import tempfile

        logger.info("Installing plugin from Git: %s", repo_url)

        with tempfile.TemporaryDirectory(prefix="calibre_plugin_git_") as temp_dir:
            temp_path = Path(temp_dir)
            repo_dir = temp_path / "repo"

            # Clone repository
            cmd = ["git", "clone", "--depth", "1"]
            if branch:
                cmd.extend(["--branch", branch])
            cmd.extend([repo_url, str(repo_dir)])

            try:
                subprocess.run(  # noqa: S603
                    cmd,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                logger.exception("Failed to clone repository: %s", e.stderr)
                msg = f"Failed to clone repository: {e.stderr}"
                raise RuntimeError(msg) from e

            # Locate plugin directory
            target_dir = repo_dir
            if plugin_path_in_repo:
                target_dir = repo_dir / plugin_path_in_repo
                if not target_dir.exists():
                    msg = (
                        f"Plugin path '{plugin_path_in_repo}' not found in repository."
                    )
                    raise RuntimeError(msg)

            # Check if target_dir has __init__.py (Calibre plugins are Python packages)
            # Or usually they are zipped directories.
            # If it's a directory, we need to zip it.

            zip_path = temp_path / "plugin.zip"

            # Create zip from directory
            # shutil.make_archive base_name is without extension
            shutil.make_archive(str(temp_path / "plugin"), "zip", root_dir=target_dir)

            if not zip_path.exists():
                msg = "Failed to create plugin ZIP."
                raise RuntimeError(msg)

            # Install the zip
            self.install_plugin(zip_path)

    def _parse_plugin_list(self, output: str) -> list[PluginInfo]:
        """Parse output from `calibre-customize -l`."""
        plugins: list[PluginInfo] = []
        current_plugin: PluginInfo | None = None

        lines = output.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if this line looks like a plugin header
            # Pattern: Name (Version) by Author
            if " (" in line and ") by " in line:
                # Save previous plugin if exists
                if current_plugin:
                    plugins.append(current_plugin)

                try:
                    # Parse header
                    # Example: DeDRM (7.2.1) by apprenticeharper
                    name_part, rest = line.split(" (", 1)
                    version_part, author_part = rest.split(") by ", 1)

                    current_plugin = {
                        "name": name_part.strip(),
                        "version": version_part.strip(),
                        "author": author_part.strip(),
                        "description": "",
                    }
                except ValueError:
                    # Failed to parse, maybe it's part of description or different format
                    if current_plugin:
                        current_plugin["description"] += " " + line
            else:
                # Description line
                if current_plugin:
                    if current_plugin["description"]:
                        current_plugin["description"] += " "
                    current_plugin["description"] += line

        # Add last plugin
        if current_plugin:
            plugins.append(current_plugin)

        return plugins
