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

import { useMemo } from "react";
import { TagInput } from "@/components/forms/TagInput";
import type { AuthorUpdate, AuthorWithMetadata } from "@/types/author";
import { categorizeGenresAndStyles } from "@/utils/genreCategorizer";

interface TagsTabProps {
  author: AuthorWithMetadata;
  form: AuthorUpdate;
  onFieldChange: <K extends keyof AuthorUpdate>(
    field: K,
    value: AuthorUpdate[K],
  ) => void;
}

/**
 * Component for the tags tab.
 *
 * Follows SRP by handling only tags-related fields.
 * Populates genres and styles from author subjects using categorizeGenresAndStyles.
 * Populates similar authors from author.similar_authors array.
 */
export function TagsTab({ author, form, onFieldChange }: TagsTabProps) {
  // Get subjects from author.genres (which are actually subjects/tags from works)
  const subjects = author.genres || [];

  // Categorize subjects into genres and styles
  const { genres: categorizedGenres, styles: categorizedStyles } = useMemo(
    () => categorizeGenresAndStyles(subjects),
    [subjects],
  );

  // Get genres: use form value if set, otherwise use categorized genres
  const displayGenres = form.genres ?? categorizedGenres;

  // Get styles: use form value if set, otherwise use categorized styles
  const displayStyles = form.styles ?? categorizedStyles;

  // Get similar authors: convert AuthorWithMetadata[] to string[] (author names)
  const similarAuthorNames = useMemo(() => {
    if (form.similar_authors) {
      return form.similar_authors;
    }
    if (author.similar_authors && author.similar_authors.length > 0) {
      return author.similar_authors.map((sa) => sa.name);
    }
    return [];
  }, [form.similar_authors, author.similar_authors]);

  // Extract OLID from author key (remove /authors/ prefix if present)
  const olid = useMemo(() => {
    if (!author.key) return "";
    return author.key.replace("/authors/", "").replace("authors/", "");
  }, [author.key]);

  const inputBaseClasses =
    "w-full min-h-[38px] rounded-md border border-surface-a20 bg-surface-a20 px-[10px] py-1.5 text-sm text-text-a0 transition-colors focus:outline-none focus:border-primary-a0 focus:bg-surface-a10 disabled:cursor-not-allowed disabled:opacity-50";
  const labelDivClasses = "font-semibold text-sm text-text-a10";

  return (
    <div className="flex h-full w-full flex-col gap-4">
      <label className="flex flex-col gap-2">
        <div className={`${labelDivClasses} flex items-center gap-2`}>
          <i className="pi pi-lock text-sm text-text-a30" aria-hidden="true" />
          <div>OLID</div>
        </div>
        <input className={inputBaseClasses} value={olid} disabled readOnly />
      </label>
      <TagInput
        id="genres"
        label="Genres"
        tags={displayGenres}
        onChange={(tags) =>
          onFieldChange("genres", tags.length > 0 ? tags : null)
        }
        placeholder="Add genres (press Enter or comma)"
        filterType="genre"
      />
      <TagInput
        id="styles"
        label="Styles"
        tags={displayStyles}
        onChange={(tags) =>
          onFieldChange("styles", tags.length > 0 ? tags : null)
        }
        placeholder="Add styles (press Enter or comma)"
        filterType="genre"
      />
      <TagInput
        id="shelves"
        label="Shelves"
        tags={form.shelves || []}
        onChange={(tags) =>
          onFieldChange("shelves", tags.length > 0 ? tags : null)
        }
        placeholder="Add shelves (press Enter or comma)"
      />
      <TagInput
        id="similar-authors"
        label="Similar Authors"
        tags={similarAuthorNames}
        onChange={(tags) =>
          onFieldChange("similar_authors", tags.length > 0 ? tags : null)
        }
        placeholder="Add similar authors (press Enter or comma)"
      />
    </div>
  );
}
