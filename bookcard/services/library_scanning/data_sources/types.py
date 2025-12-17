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

"""Type definitions for data source responses."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class IdentifierDict:
    """Dictionary of external identifiers.

    Keys are identifier types (e.g., "viaf", "goodreads", "wikidata"),
    values are identifier strings.
    """

    viaf: str | None = None
    goodreads: str | None = None
    wikidata: str | None = None
    isni: str | None = None
    librarything: str | None = None
    amazon: str | None = None
    imdb: str | None = None
    musicbrainz: str | None = None
    lc_naf: str | None = None
    opac_sbn: str | None = None
    storygraph: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert to dictionary, excluding None values.

        Returns
        -------
        dict[str, str]
            Dictionary of identifier type to value.
        """
        return {
            key: value
            for key, value in (
                ("viaf", self.viaf),
                ("goodreads", self.goodreads),
                ("wikidata", self.wikidata),
                ("isni", self.isni),
                ("librarything", self.librarything),
                ("amazon", self.amazon),
                ("imdb", self.imdb),
                ("musicbrainz", self.musicbrainz),
                ("lc_naf", self.lc_naf),
                ("opac_sbn", self.opac_sbn),
                ("storygraph", self.storygraph),
            )
            if value is not None
        }


@dataclass
class AuthorData:
    """Author data structure from external data source.

    Normalized format that can be mapped to AuthorMetadata model.
    """

    key: str
    name: str
    personal_name: str | None = None
    fuller_name: str | None = None
    title: str | None = None
    birth_date: str | None = None
    death_date: str | None = None
    entity_type: str | None = None
    biography: str | None = None
    location: str | None = None
    photo_ids: Sequence[int] = ()
    alternate_names: Sequence[str] = ()
    links: Sequence[dict[str, str]] = ()
    identifiers: IdentifierDict | None = None
    work_count: int | None = None
    ratings_average: float | None = None
    ratings_count: int | None = None
    top_work: str | None = None
    subjects: Sequence[str] = ()


@dataclass
class BookData:
    """Book data structure from external data source.

    Normalized format for book metadata.
    """

    key: str
    title: str
    authors: Sequence[str] = ()
    isbn: str | None = None
    isbn13: str | None = None
    publish_date: str | None = None
    publishers: Sequence[str] = ()
    subjects: Sequence[str] = ()
    description: str | None = None
    cover_url: str | None = None
