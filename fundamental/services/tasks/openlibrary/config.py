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

"""Configuration classes for OpenLibrary dump ingestion."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionConfig:
    """Configuration for OpenLibrary ingestion.

    Attributes
    ----------
    data_directory : str
        Base directory for data files. Defaults to "/data".
    batch_size : int
        Number of records to batch before committing. Defaults to 10000.
    process_authors : bool
        Whether to process authors dump file. Defaults to True.
    process_works : bool
        Whether to process works dump file. Defaults to True.
    process_editions : bool
        Whether to process editions dump file. Defaults to True.
    progress_update_interval : int
        Number of records processed before updating progress. Defaults to 100000.
    """

    data_directory: str = "/data"
    batch_size: int = 10000
    process_authors: bool = True
    process_works: bool = True
    process_editions: bool = True
    progress_update_interval: int = 100000
