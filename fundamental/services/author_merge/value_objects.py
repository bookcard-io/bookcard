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

"""Value objects for author merge operations.

These value objects encapsulate data structures used throughout
the author merge process, following DDD principles.
"""

from dataclasses import dataclass

from fundamental.models.author_metadata import AuthorMapping, AuthorMetadata


@dataclass
class MergeContext:
    """Context for merging two authors.

    Parameters
    ----------
    keep_author : AuthorMetadata
        Author to keep (target of merge).
    merge_author : AuthorMetadata
        Author to merge (will be deleted).
    library_id : int
        Library identifier.
    keep_mapping : AuthorMapping
        Mapping for the keep author.
    merge_mapping : AuthorMapping
        Mapping for the merge author.
    """

    keep_author: AuthorMetadata
    merge_author: AuthorMetadata
    library_id: int
    keep_mapping: AuthorMapping
    merge_mapping: AuthorMapping


@dataclass
class AuthorScore:
    """Scoring information for an author.

    Parameters
    ----------
    book_count : int
        Number of books associated with the author.
    is_verified : bool
        Whether the author mapping is verified.
    metadata_completeness : int
        Metadata completeness score.
    user_photos_count : int
        Number of user-uploaded photos.
    total : int
        Total score (calculated).
    """

    book_count: int
    is_verified: bool
    metadata_completeness: int
    user_photos_count: int
    total: int


@dataclass
class RelationshipCounts:
    """Counts of relationships for an author.

    Parameters
    ----------
    alternate_names : int
        Number of alternate names.
    remote_ids : int
        Number of remote IDs.
    photos : int
        Number of photos.
    links : int
        Number of links.
    works : int
        Number of works.
    work_subjects : int
        Number of work subjects.
    similarities : int
        Number of similarities.
    user_metadata : int
        Number of user metadata records.
    user_photos : int
        Number of user photos.
    """

    alternate_names: int
    remote_ids: int
    photos: int
    links: int
    works: int
    work_subjects: int
    similarities: int
    user_metadata: int
    user_photos: int
