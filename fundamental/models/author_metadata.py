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

"""Author metadata models for storing OpenLibrary and external author data.

These models store enriched author information from external sources (primarily
OpenLibrary) and link them to Calibre authors. This data lives outside the
Calibre metadata.db database.
"""

from datetime import UTC, datetime

from sqlalchemy import Column, Float, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


class AuthorMetadata(SQLModel, table=True):
    """Author metadata model for storing OpenLibrary author data.

    Stores enriched author information from external sources, primarily
    OpenLibrary API. Links to Calibre authors via AuthorMapping.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    openlibrary_key : str
        OpenLibrary author key (e.g., "OL23919A"). Unique identifier.
    name : str
        Author name (primary name).
    personal_name : str | None
        Personal name if different from name.
    fuller_name : str | None
        Fuller name including middle names, titles, etc.
    title : str | None
        Title (e.g., "OBE", "Sir").
    birth_date : str | None
        Birth date as string (e.g., "31 July 1965").
    death_date : str | None
        Death date as string.
    entity_type : str | None
        Entity type (e.g., "person", "corporate").
    biography : str | None
        Author biography text.
    location : str | None
        Location/country (derived from bio or other fields).
    photo_url : str | None
        Primary photo URL (derived from photos).
    work_count : int | None
        Number of works by this author.
    ratings_average : float | None
        Average rating from OpenLibrary.
    ratings_count : int | None
        Number of ratings.
    top_work : str | None
        Top/most popular work title.
    created_at : datetime
        Record creation timestamp.
    updated_at : datetime
        Last update timestamp.
    last_synced_at : datetime | None
        Last time data was synced from OpenLibrary.
    """

    __tablename__ = "author_metadata"

    id: int | None = Field(default=None, primary_key=True)
    openlibrary_key: str = Field(
        unique=True,
        index=True,
        max_length=50,
        description="OpenLibrary author key (e.g., 'OL23919A')",
    )
    name: str = Field(max_length=500, index=True)
    personal_name: str | None = Field(default=None, max_length=500)
    fuller_name: str | None = Field(default=None, max_length=500)
    title: str | None = Field(default=None, max_length=100)
    birth_date: str | None = Field(default=None, max_length=100)
    death_date: str | None = Field(default=None, max_length=100)
    entity_type: str | None = Field(default=None, max_length=50)
    biography: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    location: str | None = Field(default=None, max_length=200)
    photo_url: str | None = Field(default=None, max_length=1000)
    work_count: int | None = Field(default=None)
    ratings_average: float | None = Field(default=None)
    ratings_count: int | None = Field(default=None)
    top_work: str | None = Field(default=None, max_length=500)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )
    last_synced_at: datetime | None = Field(default=None)

    # Relationships
    remote_ids: list["AuthorRemoteId"] = Relationship(back_populates="author")
    photos: list["AuthorPhoto"] = Relationship(back_populates="author")
    alternate_names: list["AuthorAlternateName"] = Relationship(back_populates="author")
    links: list["AuthorLink"] = Relationship(back_populates="author")
    works: list["AuthorWork"] = Relationship(back_populates="author")
    mappings: list["AuthorMapping"] = Relationship(back_populates="author_metadata")
    similar_to: list["AuthorSimilarity"] = Relationship(
        back_populates="author1",
        sa_relationship_kwargs={"foreign_keys": "[AuthorSimilarity.author1_id]"},
    )
    similar_from: list["AuthorSimilarity"] = Relationship(
        back_populates="author2",
        sa_relationship_kwargs={"foreign_keys": "[AuthorSimilarity.author2_id]"},
    )

    __table_args__ = (
        Index("idx_author_metadata_name", "name"),
        Index("idx_author_metadata_openlibrary_key", "openlibrary_key"),
    )


class AuthorRemoteId(SQLModel, table=True):
    """Author remote identifier model.

    Stores external identifiers for authors (VIAF, Goodreads, Wikidata, etc.).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    identifier_type : str
        Type of identifier (e.g., "viaf", "goodreads", "wikidata", "isni").
    identifier_value : str
        Identifier value.
    """

    __tablename__ = "author_remote_ids"

    id: int | None = Field(default=None, primary_key=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    identifier_type: str = Field(max_length=50, index=True)
    identifier_value: str = Field(max_length=200, index=True)

    # Relationships
    author: AuthorMetadata = Relationship(back_populates="remote_ids")

    __table_args__ = (
        UniqueConstraint(
            "author_metadata_id", "identifier_type", name="uq_author_remote_id"
        ),
    )


class AuthorPhoto(SQLModel, table=True):
    """Author photo model.

    Stores photo information from OpenLibrary.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    openlibrary_photo_id : int | None
        Photo ID from OpenLibrary.
    photo_url : str | None
        Derived photo URL.
    is_primary : bool
        Whether this is the primary photo for the author.
    order : int
        Display order (default 0).
    """

    __tablename__ = "author_photos"

    id: int | None = Field(default=None, primary_key=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    openlibrary_photo_id: int | None = Field(default=None)
    photo_url: str | None = Field(default=None, max_length=1000)
    is_primary: bool = Field(default=False, index=True)
    order: int = Field(default=0)

    # Relationships
    author: AuthorMetadata = Relationship(back_populates="photos")


class AuthorAlternateName(SQLModel, table=True):
    """Author alternate name model.

    Stores alternate names, pen names, and name variations.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    name : str
        Alternate name.
    """

    __tablename__ = "author_alternate_names"

    id: int | None = Field(default=None, primary_key=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    name: str = Field(max_length=500, index=True)

    # Relationships
    author: AuthorMetadata = Relationship(back_populates="alternate_names")

    __table_args__ = (
        UniqueConstraint("author_metadata_id", "name", name="uq_author_alternate_name"),
    )


class AuthorLink(SQLModel, table=True):
    """Author external link model.

    Stores external links (official website, Wikipedia, etc.).

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    title : str
        Link title (e.g., "Official Site").
    url : str
        Link URL.
    link_type : str | None
        Link type (e.g., "official", "wikipedia").
    """

    __tablename__ = "author_links"

    id: int | None = Field(default=None, primary_key=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    title: str = Field(max_length=200)
    url: str = Field(max_length=1000)
    link_type: str | None = Field(default=None, max_length=50)

    # Relationships
    author: AuthorMetadata = Relationship(back_populates="links")


class AuthorWork(SQLModel, table=True):
    """Author work model.

    Stores OpenLibrary work keys associated with an author.
    Used to persist work information for similarity calculations.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    work_key : str
        OpenLibrary work key (e.g., "OL82563W").
    rank : int
        Rank/order (lower is more popular/relevant).
    """

    __tablename__ = "author_works"

    id: int | None = Field(default=None, primary_key=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    work_key: str = Field(max_length=50, index=True)
    rank: int = Field(default=0, index=True)

    # Relationships
    author: AuthorMetadata = Relationship(back_populates="works")
    subjects: list["WorkSubject"] = Relationship(back_populates="work")

    __table_args__ = (
        UniqueConstraint("author_metadata_id", "work_key", name="uq_author_work"),
        Index("idx_author_work_rank", "author_metadata_id", "rank"),
    )


class WorkSubject(SQLModel, table=True):
    """Work subject/genre model.

    Stores subjects/genres associated with a work.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author_work_id : int
        Foreign key to AuthorWork.
    subject_name : str
        Subject/genre name (e.g., "Fantasy", "Horror").
    rank : int
        Rank/order (lower is more popular).
    """

    __tablename__ = "work_subjects"

    id: int | None = Field(default=None, primary_key=True)
    author_work_id: int = Field(foreign_key="author_works.id", index=True)
    subject_name: str = Field(max_length=200, index=True)
    rank: int = Field(default=0, index=True)

    # Relationships
    work: AuthorWork = Relationship(back_populates="subjects")

    __table_args__ = (
        UniqueConstraint("author_work_id", "subject_name", name="uq_work_subject"),
        Index("idx_work_subject_rank", "author_work_id", "rank"),
    )


class AuthorMapping(SQLModel, table=True):
    """Author mapping model.

    Links Calibre authors to OpenLibrary author metadata.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    calibre_author_id : int
        Foreign key to Calibre Author (from core.Author).
    author_metadata_id : int
        Foreign key to AuthorMetadata.
    confidence_score : float | None
        Matching confidence score (0.0 to 1.0) from automated matching.
    is_verified : bool
        Whether the mapping has been manually verified.
    matched_by : str | None
        How the match was made (e.g., "name_exact", "name_fuzzy", "manual").
    created_at : datetime
        Mapping creation timestamp.
    updated_at : datetime
        Last update timestamp.
    """

    __tablename__ = "author_mappings"

    id: int | None = Field(default=None, primary_key=True)
    calibre_author_id: int = Field(index=True)
    author_metadata_id: int = Field(foreign_key="author_metadata.id", index=True)
    confidence_score: float | None = Field(
        default=None,
        sa_column=Column(Float, nullable=True),
        ge=0.0,
        le=1.0,
    )
    library_id: int = Field(foreign_key="libraries.id", index=True)
    is_verified: bool = Field(default=False, index=True)
    matched_by: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)},
    )

    # Relationships
    author_metadata: AuthorMetadata = Relationship(back_populates="mappings")

    __table_args__ = (
        Index("idx_author_mapping_calibre", "calibre_author_id"),
        Index("idx_author_mapping_metadata", "author_metadata_id"),
        Index("idx_author_mapping_verified", "is_verified"),
    )


class AuthorSimilarity(SQLModel, table=True):
    """Author similarity model.

    Stores similar authors relationships for recommendations.

    Attributes
    ----------
    id : int | None
        Primary key identifier.
    author1_id : int
        Foreign key to AuthorMetadata (first author).
    author2_id : int
        Foreign key to AuthorMetadata (second author).
    similarity_score : float
        Similarity score (0.0 to 1.0).
    similarity_source : str | None
        Source of similarity (e.g., "openlibrary", "genre_match", "collaboration").
    created_at : datetime
        Record creation timestamp.
    """

    __tablename__ = "author_similarities"

    id: int | None = Field(default=None, primary_key=True)
    author1_id: int = Field(foreign_key="author_metadata.id", index=True)
    author2_id: int = Field(foreign_key="author_metadata.id", index=True)
    similarity_score: float = Field(
        sa_column=Column(Float, nullable=False),
        ge=0.0,
        le=1.0,
    )
    similarity_source: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        index=True,
    )

    # Relationships
    author1: AuthorMetadata = Relationship(
        back_populates="similar_to",
        sa_relationship_kwargs={"foreign_keys": "[AuthorSimilarity.author1_id]"},
    )
    author2: AuthorMetadata = Relationship(
        back_populates="similar_from",
        sa_relationship_kwargs={"foreign_keys": "[AuthorSimilarity.author2_id]"},
    )

    __table_args__ = (
        UniqueConstraint("author1_id", "author2_id", name="uq_author_similarity"),
        Index("idx_author_similarity_score", "author1_id", "similarity_score"),
    )
