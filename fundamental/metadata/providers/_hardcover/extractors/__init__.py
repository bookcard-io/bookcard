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

"""Field extractors for Hardcover book data."""

from fundamental.metadata.providers._hardcover.extractors.authors import (
    AuthorsExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.cover import CoverExtractor
from fundamental.metadata.providers._hardcover.extractors.identifiers import (
    IdentifiersExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.languages import (
    LanguagesExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.published_date import (
    PublishedDateExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.publisher import (
    PublisherExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.series import (
    SeriesExtractor,
)
from fundamental.metadata.providers._hardcover.extractors.tags import TagsExtractor

__all__ = [
    "AuthorsExtractor",
    "CoverExtractor",
    "IdentifiersExtractor",
    "LanguagesExtractor",
    "PublishedDateExtractor",
    "PublisherExtractor",
    "SeriesExtractor",
    "TagsExtractor",
]
