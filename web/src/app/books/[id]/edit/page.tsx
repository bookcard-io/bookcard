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

"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { AutocompleteTextInput } from "@/components/forms/AutocompleteTextInput";
import { Button } from "@/components/forms/Button";
import { DateInput } from "@/components/forms/DateInput";
import { FormSection } from "@/components/forms/FormSection";
import { IdentifierInput } from "@/components/forms/IdentifierInput";
import { MultiTextInput } from "@/components/forms/MultiTextInput";
import { NumberInput } from "@/components/forms/NumberInput";
import { RatingInput } from "@/components/forms/RatingInput";
import { TagInput } from "@/components/forms/TagInput";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { MetadataFetchModal } from "@/components/metadata";
import { useBook } from "@/hooks/useBook";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";
import { languageFilterSuggestionsService } from "@/services/filterSuggestionsService";
import type { BookUpdate } from "@/types/book";
import {
  applyBookUpdateToForm,
  convertMetadataRecordToBookUpdate,
} from "@/utils/metadata";
import styles from "./page.module.scss";

interface BookEditPageProps {
  params: Promise<{ id: string }>;
}

/**
 * Book edit metadata page.
 *
 * Provides a comprehensive form for editing all book metadata.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 */
export default function BookEditPage({ params }: BookEditPageProps) {
  const router = useRouter();
  const [bookId, setBookId] = useState<number | null>(null);
  const { book, isLoading, error, updateBook, isUpdating, updateError } =
    useBook({
      bookId: bookId || 0,
      enabled: bookId !== null,
      full: true,
    });

  // Form state
  const [formData, setFormData] = useState<BookUpdate>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);

  // Enable scrolling on this page (global styles disable it)
  useEffect(() => {
    document.body.style.overflow = "auto";
    return () => {
      document.body.style.overflow = "hidden";
    };
  }, []);

  // Initialize book ID from params
  useEffect(() => {
    void params.then((p) => {
      const id = parseInt(p.id, 10);
      if (!Number.isNaN(id)) {
        setBookId(id);
      }
    });
  }, [params]);

  // Initialize form data when book loads
  useEffect(() => {
    if (book) {
      // Extract date part from ISO string if present
      let pubdateValue: string | null = null;
      if (book.pubdate) {
        const dateMatch = book.pubdate.match(/^(\d{4}-\d{2}-\d{2})/);
        if (dateMatch?.[1]) {
          pubdateValue = dateMatch[1];
        }
      }

      setFormData({
        title: book.title,
        pubdate: pubdateValue,
        author_names: book.authors || [],
        series_name: book.series || null,
        series_index: book.series_index ?? null,
        tag_names: book.tags || [],
        identifiers: book.identifiers || [],
        description: book.description || null,
        publisher_name: book.publisher || null,
        language_codes: book.languages || null,
        rating_value: book.rating ?? null,
      });
      setHasChanges(false);
    }
  }, [book]);

  const handleFieldChange = useCallback(
    <K extends keyof BookUpdate>(field: K, value: BookUpdate[K]) => {
      setFormData((prev) => {
        const updated = { ...prev, [field]: value };
        setHasChanges(true);
        return updated;
      });
    },
    [],
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      if (!bookId) {
        return;
      }

      // Convert date string to ISO format if provided
      const updatePayload: BookUpdate = { ...formData };
      if (updatePayload.pubdate) {
        // If it's just a date string (YYYY-MM-DD), convert to ISO
        if (
          typeof updatePayload.pubdate === "string" &&
          updatePayload.pubdate.match(/^\d{4}-\d{2}-\d{2}$/)
        ) {
          updatePayload.pubdate = `${updatePayload.pubdate}T00:00:00Z`;
        }
      }

      // Clean up empty arrays - convert to null for backend
      const cleanedPayload: BookUpdate = { ...updatePayload };
      if (
        cleanedPayload.author_names &&
        cleanedPayload.author_names.length === 0
      ) {
        cleanedPayload.author_names = null;
      }
      if (cleanedPayload.tag_names && cleanedPayload.tag_names.length === 0) {
        cleanedPayload.tag_names = null;
      }
      if (
        cleanedPayload.identifiers &&
        cleanedPayload.identifiers.length === 0
      ) {
        cleanedPayload.identifiers = null;
      }
      if (
        cleanedPayload.language_codes &&
        cleanedPayload.language_codes.length === 0
      ) {
        cleanedPayload.language_codes = null;
      }

      const updated = await updateBook(cleanedPayload);
      if (updated) {
        setHasChanges(false);
        setShowSuccess(true);
        // Hide success message after 3 seconds
        setTimeout(() => setShowSuccess(false), 3000);
      }
    },
    [bookId, formData, updateBook],
  );

  const handleCancel = useCallback(() => {
    router.back();
  }, [router]);

  /**
   * Handles metadata record selection and populates the form.
   *
   * Parameters
   * ----------
   * record : MetadataRecord
   *     Metadata record from external source.
   */
  const handleSelectMetadata = useCallback(
    (record: MetadataRecord) => {
      const update = convertMetadataRecordToBookUpdate(record);
      applyBookUpdateToForm(update, handleFieldChange);

      // Close the metadata modal after selection
      setShowMetadataModal(false);
    },
    [handleFieldChange],
  );

  if (isLoading) {
    return (
      <div className={styles.container}>
        <div className={styles.loading}>Loading book data...</div>
      </div>
    );
  }

  if (error || !book) {
    return (
      <div className={styles.container}>
        <div className={styles.error}>
          {error || "Book not found"}
          <Button onClick={handleCancel} variant="secondary" size="medium">
            Go Back
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <button
            type="button"
            onClick={handleCancel}
            className={styles.backButton}
            aria-label="Go back"
          >
            ← Back
          </button>
          <div className={styles.titleRow}>
            <h1 className={styles.title}>Edit Book Metadata</h1>
            <Button
              type="button"
              variant="success"
              size="medium"
              onClick={() => setShowMetadataModal(true)}
              disabled={isUpdating}
            >
              Fetch metadata
            </Button>
          </div>
        </div>
        {book.thumbnail_url && (
          <div className={styles.coverPreview}>
            <ImageWithLoading
              src={book.thumbnail_url}
              alt={`Cover for ${book.title}`}
              width={120}
              height={180}
              className={styles.cover}
              unoptimized
            />
          </div>
        )}
      </div>

      {showMetadataModal && (
        <MetadataFetchModal
          book={book}
          onClose={() => setShowMetadataModal(false)}
          onSelectMetadata={handleSelectMetadata}
        />
      )}

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.formCard}>
          {/* Basic Information Section */}
          <FormSection
            title="Basic Information"
            description="Core book details"
          >
            <TextInput
              id="title"
              label="Title"
              value={formData.title || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleFieldChange("title", e.target.value)
              }
              required
            />
            <MultiTextInput
              id="authors"
              label="Authors"
              values={formData.author_names || []}
              onChange={(authors) => handleFieldChange("author_names", authors)}
              placeholder="Add author names (press Enter or comma)"
              filterType="author"
            />
            <DateInput
              id="pubdate"
              label="Publication Date"
              value={formData.pubdate || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleFieldChange("pubdate", e.target.value || null)
              }
            />
            <TextArea
              id="description"
              label="Description"
              value={formData.description || ""}
              onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                handleFieldChange("description", e.target.value || null)
              }
              placeholder="Enter book description..."
              rows={6}
              wrapperClassName={styles.fullWidth}
            />
          </FormSection>

          {/* Series Information Section */}
          <FormSection
            title="Series Information"
            description="Series name and position"
          >
            <AutocompleteTextInput
              id="series_name"
              label="Series Name"
              value={formData.series_name || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleFieldChange(
                  "series_name",
                  (e.target as HTMLInputElement).value || null,
                )
              }
              placeholder="Enter series name"
              filterType="series"
            />
            <NumberInput
              id="series_index"
              label="Series Index"
              value={formData.series_index ?? ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleFieldChange(
                  "series_index",
                  e.target.value ? parseFloat(e.target.value) : null,
                )
              }
              step={0.1}
              min={0}
              helperText="Position in series (e.g., 1.2 for volume 1, book 2)"
            />
          </FormSection>

          {/* Classification Section */}
          <FormSection
            title="Classification"
            description="Tags, identifiers, and ratings"
          >
            <TagInput
              id="tags"
              label="Tags"
              tags={formData.tag_names || []}
              onChange={(tags) => handleFieldChange("tag_names", tags)}
              placeholder="Add tags (press Enter or comma)"
              filterType="genre"
            />
            <IdentifierInput
              id="identifiers"
              label="Identifiers"
              identifiers={formData.identifiers || []}
              onChange={(identifiers) =>
                handleFieldChange("identifiers", identifiers)
              }
            />
            <RatingInput
              id="rating"
              label="Rating"
              value={formData.rating_value ?? null}
              onChange={(rating) => handleFieldChange("rating_value", rating)}
            />
          </FormSection>

          {/* Additional Metadata Section */}
          <FormSection
            title="Additional Metadata"
            description="Publisher and language"
          >
            <AutocompleteTextInput
              id="publisher"
              label="Publisher"
              value={formData.publisher_name || ""}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleFieldChange(
                  "publisher_name",
                  (e.target as HTMLInputElement).value || null,
                )
              }
              placeholder="Enter publisher name"
              filterType="publisher"
            />
            <TagInput
              id="languages"
              label="Languages (ISO 639-1 language code)"
              tags={formData.language_codes || []}
              onChange={(languages) =>
                handleFieldChange(
                  "language_codes",
                  languages.length > 0 ? languages : null,
                )
              }
              placeholder="Add language code"
              filterType="language"
              suggestionsService={languageFilterSuggestionsService}
            />
          </FormSection>
        </div>

        <div className={styles.actions}>
          <div className={styles.statusMessages}>
            {updateError && (
              <div className={styles.errorBanner} role="alert">
                {updateError}
              </div>
            )}

            {showSuccess && (
              <div className={styles.successBanner}>
                Book metadata updated successfully!
              </div>
            )}
          </div>
          <div className={styles.actionButtons}>
            <Button
              type="button"
              variant="ghost"
              size="medium"
              onClick={handleCancel}
              disabled={isUpdating}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="medium"
              loading={isUpdating}
              disabled={!hasChanges}
            >
              Save changes
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
