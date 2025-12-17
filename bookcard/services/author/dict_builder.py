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

"""Author dictionary builder following Builder pattern.

Encapsulates complex author serialization logic.
"""

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from bookcard.models.author_metadata import (
    AuthorAlternateName,
    AuthorLink,
    AuthorMapping,
    AuthorMetadata,
    AuthorPhoto,
    AuthorRemoteId,
    AuthorUserMetadata,
    AuthorUserPhoto,
    AuthorWork,
)


class AuthorDictBuilder:
    """Builder for creating author dictionaries from AuthorMetadata objects."""

    def __init__(self, session: Session) -> None:  # type: ignore[type-arg]
        """Initialize author dict builder.

        Parameters
        ----------
        session : Session
            Database session for loading relationships.
        """
        self._session = session

    def build(self, author: AuthorMetadata) -> dict[str, object]:
        """Build author dictionary for response.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, object]
            Author data dictionary matching OpenLibrary format.
        """
        # Handle unmatched authors (transient objects without AuthorMapping)
        calibre_id = getattr(author, "_calibre_id", None)
        if author.id is None and calibre_id is not None:
            return self._build_unmatched_transient_dict(author, calibre_id)

        # Handle unmatched authors that have been persisted
        if author.openlibrary_key is None:
            return self._build_unmatched_persisted_dict(author)

        # Handle matched authors with OpenLibrary key
        return self._build_matched_dict(author)

    def _build_unmatched_transient_dict(
        self, author: AuthorMetadata, calibre_id: int
    ) -> dict[str, object]:
        """Build dictionary for transient unmatched author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.
        calibre_id : int
            Calibre author ID.

        Returns
        -------
        dict[str, object]
            Author data dictionary.
        """
        return {
            "name": author.name,
            "key": f"calibre-{calibre_id}",
            "calibre_id": calibre_id,
            "is_unmatched": True,
            "location": "Local Library (Unmatched)",
        }

    def _build_unmatched_persisted_dict(
        self, author: AuthorMetadata
    ) -> dict[str, object]:
        """Build dictionary for persisted unmatched author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, object]
            Author data dictionary.
        """
        key = f"local-{author.id}"
        calibre_id = None

        # Load mappings if not present
        if not getattr(author, "mappings", None):
            author.mappings = list(
                self._session.exec(
                    select(AuthorMapping).where(
                        AuthorMapping.author_metadata_id == author.id
                    )
                ).all()
            )

        if getattr(author, "mappings", None):
            calibre_id = author.mappings[0].calibre_author_id
            key = f"calibre-{calibre_id}"

        # Ensure relationships are loaded
        self._ensure_relationships_loaded(author)

        # Load user photos if not already loaded
        if not hasattr(author, "user_photos") or author.user_photos is None:
            author.user_photos = list(
                self._session.exec(
                    select(AuthorUserPhoto).where(
                        AuthorUserPhoto.author_metadata_id == author.id
                    )
                ).all()
            )

        # Build component dictionaries and lists
        remote_ids = self._build_remote_ids_dict(author)
        photos = self._build_photos_list(author)
        alternate_names = [alt_name.name for alt_name in author.alternate_names]
        links = self._build_links_list(author)
        subjects = self._build_subjects_list(author)
        bio = self._build_bio_dict(author.biography)

        # Build author object
        author_data: dict[str, object] = {
            "name": author.name,
            "key": key,
            "calibre_id": calibre_id,
            "is_unmatched": True,
            "location": author.location or "Local Library (Unmatched)",
        }

        # Add optional fields
        self._add_optional_fields(
            author_data,
            author,
            bio,
            remote_ids,
            photos,
            alternate_names,
            links,
            subjects,
        )

        # Add user photos
        self._add_user_photos_field(author_data, author)

        return author_data

    def _build_matched_dict(self, author: AuthorMetadata) -> dict[str, object]:
        """Build dictionary for matched author with OpenLibrary key.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, object]
            Author data dictionary.
        """
        # Ensure relationships are loaded
        self._ensure_relationships_loaded(author)

        # Load mappings to get calibre_id
        if not getattr(author, "mappings", None):
            author.mappings = list(
                self._session.exec(
                    select(AuthorMapping).where(
                        AuthorMapping.author_metadata_id == author.id
                    )
                ).all()
            )

        calibre_id = None
        if getattr(author, "mappings", None):
            calibre_id = author.mappings[0].calibre_author_id

        # Load user metadata if not already loaded
        if not hasattr(author, "user_metadata") or author.user_metadata is None:
            author.user_metadata = list(
                self._session.exec(
                    select(AuthorUserMetadata).where(
                        AuthorUserMetadata.author_metadata_id == author.id
                    )
                ).all()
            )

        # Load user photos if not already loaded
        if not hasattr(author, "user_photos") or author.user_photos is None:
            author.user_photos = list(
                self._session.exec(
                    select(AuthorUserPhoto).where(
                        AuthorUserPhoto.author_metadata_id == author.id
                    )
                ).all()
            )

        # Build component dictionaries and lists
        remote_ids = self._build_remote_ids_dict(author)
        photos = self._build_photos_list(author)
        alternate_names = [alt_name.name for alt_name in author.alternate_names]
        links = self._build_links_list(author)
        subjects = self._build_subjects_list(author)
        bio = self._build_bio_dict(author.biography)

        # Build author object matching OpenLibrary format
        author_data: dict[str, object] = {
            "name": author.name,
            "key": author.openlibrary_key,
            "calibre_id": calibre_id,
        }

        # Add optional fields
        self._add_optional_fields(
            author_data,
            author,
            bio,
            remote_ids,
            photos,
            alternate_names,
            links,
            subjects,
        )

        # Add user-defined metadata (overrides auto-populated)
        self._add_user_metadata_fields(author_data, author)

        # Add user photos (and possibly override photo_url)
        self._add_user_photos_field(author_data, author)

        return author_data

    def _build_remote_ids_dict(self, author: AuthorMetadata) -> dict[str, str]:
        """Build remote IDs dictionary.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        dict[str, str]
            Dictionary mapping identifier type to value.
        """
        return {
            remote_id.identifier_type: remote_id.identifier_value
            for remote_id in author.remote_ids
        }

    def _build_photos_list(self, author: AuthorMetadata) -> list[int]:
        """Build photos list from author photos.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[int]
            List of OpenLibrary photo IDs.
        """
        return [
            photo.openlibrary_photo_id
            for photo in author.photos
            if photo.openlibrary_photo_id and photo.openlibrary_photo_id > 0
        ]

    def _build_links_list(self, author: AuthorMetadata) -> list[dict[str, str]]:
        """Build links list from author links.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[dict[str, str]]
            List of link dictionaries.
        """
        return [
            {
                "title": link.title or "",
                "url": link.url,
                "type": {"key": link.link_type or "/type/link"},
            }
            for link in author.links
        ]

    def _build_subjects_list(self, author: AuthorMetadata) -> list[str]:
        """Build subjects list from author works.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.

        Returns
        -------
        list[str]
            Sorted list of unique subject names.
        """
        subjects_set: set[str] = set()
        for work in author.works:
            for subject in work.subjects:
                subjects_set.add(subject.subject_name)
        return sorted(subjects_set)

    def _build_bio_dict(self, biography: str | None) -> dict[str, str] | None:
        """Build bio dictionary if biography exists.

        Parameters
        ----------
        biography : str | None
            Biography text.

        Returns
        -------
        dict[str, str] | None
            Bio dictionary or None.
        """
        if not biography:
            return None
        return {"type": "/type/text", "value": biography}

    def _add_optional_fields(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
        bio: dict[str, str] | None,
        remote_ids: dict[str, str],
        photos: list[int],
        alternate_names: list[str],
        links: list[dict[str, str]],
        subjects: list[str],
    ) -> None:
        """Add optional fields to author data dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record.
        bio : dict[str, str] | None
            Bio dictionary.
        remote_ids : dict[str, str]
            Remote IDs dictionary.
        photos : list[int]
            Photos list.
        alternate_names : list[str]
            Alternate names list.
        links : list[dict[str, str]]
            Links list.
        subjects : list[str]
            Subjects list.
        """
        # Add author metadata fields
        self._add_author_metadata_fields(author_data, author)

        # Add relationship fields
        self._add_relationship_fields(
            author_data, bio, remote_ids, photos, alternate_names, links, subjects
        )

    def _add_author_metadata_fields(
        self, author_data: dict[str, object], author: AuthorMetadata
    ) -> None:
        """Add author metadata fields to dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record.
        """
        field_mapping = {
            "personal_name": author.personal_name,
            "fuller_name": author.fuller_name,
            "title": author.title,
            "entity_type": author.entity_type,
            "birth_date": author.birth_date,
            "death_date": author.death_date,
            "photo_url": author.photo_url,
            "location": author.location,
        }
        # Filter out None/empty values and update dictionary
        author_data.update({
            key: value for key, value in field_mapping.items() if value
        })

    def _add_relationship_fields(
        self,
        author_data: dict[str, object],
        bio: dict[str, str] | None,
        remote_ids: dict[str, str],
        photos: list[int],
        alternate_names: list[str],
        links: list[dict[str, str]],
        subjects: list[str],
    ) -> None:
        """Add relationship fields to dictionary.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        bio : dict[str, str] | None
            Bio dictionary.
        remote_ids : dict[str, str]
            Remote IDs dictionary.
        photos : list[int]
            Photos list.
        alternate_names : list[str]
            Alternate names list.
        links : list[dict[str, str]]
            Links list.
        subjects : list[str]
            Subjects list.
        """
        if bio:
            author_data["bio"] = bio
        if remote_ids:
            author_data["remote_ids"] = remote_ids
        if photos:
            author_data["photos"] = photos
        if alternate_names:
            author_data["alternate_names"] = alternate_names
        if links:
            author_data["links"] = links
        if subjects:
            author_data["genres"] = subjects

    def _add_user_metadata_fields(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
    ) -> None:
        """Add user-defined metadata fields to dictionary.

        User-defined fields override auto-populated values.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record with user_metadata loaded.
        """
        if not hasattr(author, "user_metadata") or not author.user_metadata:
            return

        # Check for user-defined genres
        user_genres = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "genres" and um.is_user_defined
            ),
            None,
        )
        if user_genres and isinstance(user_genres, list):
            author_data["genres"] = user_genres

        # Check for user-defined styles
        user_styles = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "styles" and um.is_user_defined
            ),
            None,
        )
        if user_styles and isinstance(user_styles, list):
            author_data["styles"] = user_styles

        # Check for user-defined shelves
        user_shelves = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "shelves" and um.is_user_defined
            ),
            None,
        )
        if user_shelves and isinstance(user_shelves, list):
            author_data["shelves"] = user_shelves

        # Check for user-defined similar_authors
        user_similar = next(
            (
                um.field_value
                for um in author.user_metadata
                if um.field_name == "similar_authors" and um.is_user_defined
            ),
            None,
        )
        if user_similar is not None and isinstance(user_similar, list):
            author_data["similar_authors"] = user_similar

    def _add_user_photos_field(
        self,
        author_data: dict[str, object],
        author: AuthorMetadata,
    ) -> None:
        """Add user-uploaded photos to author data.

        Parameters
        ----------
        author_data : dict[str, object]
            Author data dictionary to update.
        author : AuthorMetadata
            Author metadata record with user_photos loaded.
        """
        if not hasattr(author, "user_photos") or not author.user_photos:
            return

        photos_payload: list[dict[str, object]] = []
        for photo in author.user_photos:
            if photo.id is None:
                continue

            photo_url = f"/api/authors/{author.id}/photos/{photo.id}"
            photos_payload.append(
                {
                    "id": photo.id,
                    "photo_url": photo_url,
                    "file_name": photo.file_name,
                    "file_path": photo.file_path,
                    "is_primary": photo.is_primary,
                    "order": photo.order,
                    "created_at": photo.created_at.isoformat(),
                },
            )

        if photos_payload:
            author_data["user_photos"] = photos_payload

        # Ensure primary user photo becomes the main photo_url if not already set
        if "photo_url" not in author_data:
            primary_photo = next(
                (up for up in author.user_photos if up.is_primary),
                None,
            )
            if primary_photo and primary_photo.id is not None:
                author_data["photo_url"] = (
                    f"/api/authors/{author.id}/photos/{primary_photo.id}"
                )

    def _ensure_relationships_loaded(
        self,
        author: AuthorMetadata,
    ) -> None:
        """Ensure all relationships are loaded for an author.

        Parameters
        ----------
        author : AuthorMetadata
            Author metadata record.
        """
        if not author.remote_ids:
            author.remote_ids = list(
                self._session.exec(
                    select(AuthorRemoteId).where(
                        AuthorRemoteId.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.photos:
            author.photos = list(
                self._session.exec(
                    select(AuthorPhoto).where(
                        AuthorPhoto.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.alternate_names:
            author.alternate_names = list(
                self._session.exec(
                    select(AuthorAlternateName).where(
                        AuthorAlternateName.author_metadata_id == author.id
                    )
                ).all()
            )
        if not author.links:
            author.links = list(
                self._session.exec(
                    select(AuthorLink).where(AuthorLink.author_metadata_id == author.id)
                ).all()
            )
        if not author.works:
            # Load works with subjects
            works = list(
                self._session.exec(
                    select(AuthorWork)
                    .where(AuthorWork.author_metadata_id == author.id)
                    .options(selectinload(AuthorWork.subjects))
                ).all()
            )
            author.works = works
