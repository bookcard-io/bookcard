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

"""Metadata import format strategies.

This package provides format-specific importers following the Strategy pattern,
allowing easy extension with new formats while maintaining SRP and Open/Closed Principle.
"""

from bookcard.services.metadata_importers.base import MetadataImporter
from bookcard.services.metadata_importers.opf_importer import OpfImporter
from bookcard.services.metadata_importers.yaml_importer import YamlImporter

__all__ = [
    "MetadataImporter",
    "OpfImporter",
    "YamlImporter",
]
