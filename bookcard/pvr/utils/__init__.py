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

"""Utility modules for PVR system."""

from bookcard.pvr.utils.auth import build_basic_auth_header
from bookcard.pvr.utils.progress import ETACalculator, ProgressCalculator
from bookcard.pvr.utils.quality import infer_quality_from_title
from bookcard.pvr.utils.status import (
    DownloadStatus,
    StatusMapper,
    StatusMappingPresets,
)
from bookcard.pvr.utils.torrent import extract_hash_from_magnet
from bookcard.pvr.utils.xml_parser import extract_publish_date_from_xml

__all__ = [
    "DownloadStatus",
    "ETACalculator",
    "ProgressCalculator",
    "StatusMapper",
    "StatusMappingPresets",
    "build_basic_auth_header",
    "extract_hash_from_magnet",
    "extract_publish_date_from_xml",
    "infer_quality_from_title",
]
