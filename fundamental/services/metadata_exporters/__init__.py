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

"""Metadata export format strategies.

This package provides format-specific exporters following the Strategy pattern,
allowing easy extension with new formats while maintaining SRP and Open/Closed Principle.
"""

from fundamental.services.metadata_exporters.base import MetadataExporter
from fundamental.services.metadata_exporters.json_exporter import JsonExporter
from fundamental.services.metadata_exporters.opf_exporter import OpfExporter
from fundamental.services.metadata_exporters.yaml_exporter import YamlExporter

__all__ = [
    "JsonExporter",
    "MetadataExporter",
    "OpfExporter",
    "YamlExporter",
]
