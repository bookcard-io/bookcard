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

"""OPDS feed services.

Services for generating OPDS (Open Publication Distribution System) feeds
for e-reader app compatibility.
"""

from bookcard.api.schemas.opds import (
    OpdsEntry,
    OpdsFeedRequest,
    OpdsFeedResponse,
    OpdsLink,
)
from bookcard.services.opds.auth_service import OpdsAuthService
from bookcard.services.opds.book_query_service import OpdsBookQueryService
from bookcard.services.opds.feed_service import OpdsFeedService
from bookcard.services.opds.interfaces import (
    IOpdsAuthProvider,
    IOpdsBookQueryService,
    IOpdsFeedService,
    IOpdsXmlBuilder,
)
from bookcard.services.opds.url_builder import OpdsUrlBuilder
from bookcard.services.opds.xml_builder import OpdsXmlBuilder

__all__ = [
    "IOpdsAuthProvider",
    "IOpdsBookQueryService",
    "IOpdsFeedService",
    "IOpdsXmlBuilder",
    "OpdsAuthService",
    "OpdsBookQueryService",
    "OpdsEntry",
    "OpdsFeedRequest",
    "OpdsFeedResponse",
    "OpdsFeedService",
    "OpdsLink",
    "OpdsUrlBuilder",
    "OpdsXmlBuilder",
]
