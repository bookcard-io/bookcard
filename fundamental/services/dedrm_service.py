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

"""DeDRM Service.

This service handles the removal of DRM from e-books using Calibre's DeDRM plugin.
It creates a temporary Calibre library, adds the book to it (which triggers the DeDRM plugin),
and then retrieves the processed file.
"""

import json
import logging
import os
import shutil
import subprocess  # noqa: S404
import tempfile
from pathlib import Path
from typing import NoReturn

logger = logging.getLogger(__name__)


def _raise_dedrm_error(message: str) -> NoReturn:
    """Raise a DeDRM processing error.

    Centralized function for raising DeDRM errors to follow DRY
    and satisfy linter requirements for abstracting raise statements.

    DeDRM errors are runtime failures during the DRM removal process
    (e.g., calibredb command failures, file system issues, missing files).

    Parameters
    ----------
    message : str
        Error message describing the DeDRM failure.

    Raises
    ------
    RuntimeError
        Always raises with the provided error message.
    """
    raise RuntimeError(message)


class DeDRMService:
    """Service for removing DRM from e-books using Calibre plugins.

    This service relies on the DeDRM plugin being installed in Calibre.
    It works by creating a temporary library and adding the book to it using `calibredb add`.
    This triggers Calibre's import plugins, including DeDRM.
    """

    def get_config_path(self) -> Path:
        """Get the path to the DeDRM plugin configuration file.

        Returns
        -------
        Path
            Path to ``dedrm.json``.
        """
        # DeDRM stores its preferences via Calibre's JSONConfig. The upstream plugin
        # derives the filename from the plugin name lowercased, so "DeDRM" becomes
        # "dedrm.json" under the calibre plugins directory.
        config_dir = os.environ.get("CALIBRE_CONFIG_DIRECTORY")
        base_dir = (
            Path(config_dir) if config_dir else (Path.home() / ".config" / "calibre")
        )
        return base_dir / "plugins" / "dedrm.json"

    def update_configuration(self, serial_numbers: list[str]) -> None:
        """Update DeDRM configuration with serial numbers.

        Parameters
        ----------
        serial_numbers : list[str]
            List of E-Ink Kindle serial numbers.
        """
        config_path = self.get_config_path()
        config: dict[str, object] = {}
        if config_path.exists():
            try:
                with config_path.open() as f:
                    loaded = json.load(f)
                if isinstance(loaded, dict):
                    config = loaded
                else:
                    logger.warning(
                        "Unexpected DeDRM config format in %s (expected object), ignoring",
                        config_path,
                    )
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(
                    "Failed to load existing DeDRM config from %s: %s", config_path, e
                )

        # For Kindle eInk devices, DeDRM expects device serials in the "serials" list.
        serials_obj = config.get("serials", [])
        if not isinstance(serials_obj, list):
            serials_obj = []
        serials: list[str] = [s for s in serials_obj if isinstance(s, str)]

        existing_serials = set(serials)
        for serial in serial_numbers:
            cleaned = serial.strip()
            if cleaned and cleaned not in existing_serials:
                serials.append(cleaned)
                existing_serials.add(cleaned)

        config["serials"] = serials

        # Mark as configured to align with DeDRM's preference semantics.
        config["configured"] = True

        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with config_path.open("w") as f:
                json.dump(config, f, indent=2, sort_keys=True)
            logger.info("Updated DeDRM configuration at %s", config_path)
        except OSError as e:
            logger.exception("Failed to write DeDRM config at %s", config_path)
            msg = f"Failed to write DeDRM config at {config_path}: {e}"
            raise RuntimeError(msg) from e

    def strip_drm(self, file_path: Path) -> Path:
        """Attempt to strip DRM from a book file.

        Parameters
        ----------
        file_path : Path
            Path to the DRM-protected file.

        Returns
        -------
        Path
            Path to the processed file (which may be DRM-free).
            If processing fails or no change occurs, returns the path to a copy of the original file
            or the processed file if it was successfully added but not dedrmed (though that shouldn't happen if it has DRM).
            Actually, it returns the path to the file extracted from the temp library.

        Raises
        ------
        RuntimeError
            If `calibredb` is not available or execution fails.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        # Create a temporary directory for the library
        with tempfile.TemporaryDirectory(prefix="dedrm_lib_") as temp_dir:
            temp_lib_path = Path(temp_dir)

            logger.info("Created temporary library at %s for DeDRM", temp_lib_path)

            try:
                # Add book to temporary library using calibredb
                # --with-library specifies the library path
                # --duplicates tells it to add even if it thinks it's a duplicate (empty lib so unlikely, but good practice)
                cmd = [
                    "calibredb",
                    "add",
                    "--with-library",
                    str(temp_lib_path),
                    "--duplicates",
                    str(file_path),
                ]

                logger.debug("Running command: %s", " ".join(cmd))
                result = subprocess.run(  # noqa: S603
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,  # We check returncode manually
                )

                if result.returncode != 0:
                    logger.error("calibredb add failed: %s", result.stderr)
                    # If failed, return original file (copy to a temp location so caller can manage it?)
                    # The contract says "Returns the path to the processed file".
                    # If we fail, we should probably raise or return original.
                    # Let's log and return original for now, but usually we want to know if it failed.
                    msg = f"calibredb failed: {result.stderr}"
                    _raise_dedrm_error(msg)

                # Find the added book in the temp library
                # Structure is usually Author/Title (ID)/file.ext
                # But we don't know the author/title Calibre extracted.
                # However, since it's a new library with 1 book, we can just search for files.

                # Filter for the file extension we put in
                original_ext = file_path.suffix.lower()

                # Search recursively in the temp library
                added_files = list(temp_lib_path.rglob(f"*{original_ext}"))

                # Filter out metadata.db and cover.jpg
                book_files = [
                    f
                    for f in added_files
                    if f.name != "metadata.db" and f.name != "cover.jpg" and f.is_file()
                ]

                if not book_files:
                    logger.warning("No book file found in temp library after add.")
                    # This might happen if Calibre converted it or something failed silently.
                    # Or maybe the extension changed?
                    # Let's try finding any file that is not DB/cover/json/opf
                    all_files = [
                        f
                        for f in temp_lib_path.rglob("*")
                        if f.is_file()
                        and f.name
                        not in [
                            "metadata.db",
                            "metadata_db_prefs_backup.json",
                            "cover.jpg",
                        ]
                        and f.suffix.lower() not in [".opf", ".json"]
                    ]
                    if all_files:
                        book_files = all_files
                    else:
                        msg = "Book file not found in temporary library after ingest."
                        _raise_dedrm_error(msg)

                processed_file = book_files[0]
                logger.info("Found processed file: %s", processed_file)

                # We need to move this file out of the temp dir before it gets deleted
                # Create a persistent temp file for the result
                output_fd, output_path = tempfile.mkstemp(suffix=processed_file.suffix)
                # Close the fd immediately, we just need the path
                import os

                os.close(output_fd)
                output_path_obj = Path(output_path)

                shutil.copy2(processed_file, output_path_obj)
                logger.info(
                    "Copied processed file to safe location: %s", output_path_obj
                )
            except Exception:
                logger.exception("Error during DeDRM process")
                raise
            else:
                return output_path_obj
