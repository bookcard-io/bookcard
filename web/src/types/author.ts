// Copyright (C) 2025 knguyen and others
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

/**
 * TypeScript types for author-related data structures.
 *
 * These types are based on the OpenLibrary API structure.
 */

export interface AuthorBio {
  /** Type of bio content. */
  type: string;
  /** Bio text content. */
  value: string;
}

export interface AuthorRemoteIds {
  /** VIAF identifier. */
  viaf?: string;
  /** Goodreads identifier. */
  goodreads?: string;
  /** StoryGraph identifier. */
  storygraph?: string;
  /** ISNI identifier. */
  isni?: string;
  /** LibraryThing identifier. */
  librarything?: string;
  /** Amazon identifier. */
  amazon?: string;
  /** Wikidata identifier. */
  wikidata?: string;
  /** IMDB identifier. */
  imdb?: string;
  /** MusicBrainz identifier. */
  musicbrainz?: string;
  /** Library of Congress NAF identifier. */
  lc_naf?: string;
  /** OPAC SBN identifier. */
  opac_sbn?: string;
}

export interface AuthorLink {
  /** Link title. */
  title: string;
  /** Link URL. */
  url: string;
  /** Link type. */
  type: {
    key: string;
  };
}

/**
 * Author data structure matching OpenLibrary API format.
 */
export interface Author {
  /** Author name. */
  name: string;
  /** Personal name (if different from name). */
  personal_name?: string;
  /** Fuller name. */
  fuller_name?: string;
  /** Title (e.g., "OBE"). */
  title?: string;
  /** Biography information. */
  bio?: AuthorBio;
  /** Remote identifiers. */
  remote_ids?: AuthorRemoteIds;
  /** Photo IDs from OpenLibrary. */
  photos?: number[];
  /** Alternate names/pen names. */
  alternate_names?: string[];
  /** External links. */
  links?: AuthorLink[];
  /** Source records. */
  source_records?: string[];
  /** Entity type. */
  entity_type?: string;
  /** Birth date. */
  birth_date?: string;
  /** Death date. */
  death_date?: string;
  /** Author key (OpenLibrary identifier). */
  key?: string;
  /** Latest revision number. */
  latest_revision?: number;
  /** Revision number. */
  revision?: number;
  /** Created timestamp. */
  created?: {
    type: string;
    value: string;
  };
  /** Last modified timestamp. */
  last_modified?: {
    type: string;
    value: string;
  };
}

/**
 * Author with additional metadata for display.
 */
export interface AuthorWithMetadata extends Author {
  /** Photo URL (derived from photos array). */
  photo_url?: string | null;
  /** Location/country (derived from bio or other fields). */
  location?: string;
  /** Genres/styles associated with author. */
  genres?: string[];
  /** Popular books by this author (deprecated - use library books instead). */
  popular_books?: Array<{
    id: number;
    title: string;
    series?: string;
    duration?: string;
    thumbnail_url?: string | null;
  }>;
  /** Collaboration books (books with multiple authors including this one). */
  collaborations?: Array<{
    id: number;
    title: string;
    authors: string[];
    thumbnail_url?: string | null;
  }>;
  /** Similar authors. */
  similar_authors?: AuthorWithMetadata[];
}
