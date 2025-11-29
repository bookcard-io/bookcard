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

"""Metadata enforcement services.

Services for automatically enforcing metadata and cover changes to ebook files.
"""

from fundamental.services.metadata_enforcement.cover_enforcer import (
    CoverEnforcementService,
)
from fundamental.services.metadata_enforcement.ebook_enforcer import (
    EbookMetadataEnforcer,
)
from fundamental.services.metadata_enforcement.epub_enforcer import (
    EpubMetadataEnforcer,
)
from fundamental.services.metadata_enforcement.opf_enforcer import (
    OpfEnforcementService,
)

__all__ = [
    "CoverEnforcementService",
    "EbookMetadataEnforcer",
    "EpubMetadataEnforcer",
    "OpfEnforcementService",
]
