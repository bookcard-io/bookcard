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

"""File preparation service for PVR import."""

import logging
import shutil
from contextlib import suppress
from pathlib import Path

logger = logging.getLogger(__name__)


class FilePreparationService:
    """Handles file extraction and preparation."""

    def prepare_files(self, source_path: Path, dest_dir: Path) -> None:
        """Extract archives or copy files to staging directory.

        Parameters
        ----------
        source_path : Path
            Source file or directory.
        dest_dir : Path
            Destination directory.
        """
        if source_path.is_file():
            if self._is_archive(source_path):
                logger.info("Extracting archive %s to %s", source_path, dest_dir)
                shutil.unpack_archive(source_path, dest_dir)
            else:
                logger.info("Copying file %s to %s", source_path, dest_dir)
                shutil.copy2(source_path, dest_dir)
        elif source_path.is_dir():
            logger.info("Copying directory %s to %s", source_path, dest_dir)
            for item in source_path.iterdir():
                if item.is_dir():
                    shutil.copytree(item, dest_dir / item.name)
                else:
                    shutil.copy2(item, dest_dir)
                    if self._is_archive(item):
                        # Try to extract archives found inside the dir too
                        with suppress(shutil.ReadError, ValueError):
                            extract_dir = dest_dir / item.stem
                            extract_dir.mkdir(exist_ok=True)
                            shutil.unpack_archive(item, extract_dir)

    def _is_archive(self, path: Path) -> bool:
        """Check if file is a supported archive format."""
        # extensions supported by shutil.unpack_archive
        archive_extensions = {".zip", ".tar", ".gztar", ".bztar", ".xztar", ".rar"}
        return (
            path.suffix.lower() in archive_extensions or path.suffix.lower() == ".rar"
        )
