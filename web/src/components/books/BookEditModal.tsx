"use client";

import Image from "next/image";
import { useCallback, useEffect, useState } from "react";
import { AutocompleteTextInput } from "@/components/forms/AutocompleteTextInput";
import { Button } from "@/components/forms/Button";
import { DateInput } from "@/components/forms/DateInput";
import { IdentifierInput } from "@/components/forms/IdentifierInput";
import { MultiTextInput } from "@/components/forms/MultiTextInput";
import { NumberInput } from "@/components/forms/NumberInput";
import { RatingInput } from "@/components/forms/RatingInput";
import { TagInput } from "@/components/forms/TagInput";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { MetadataFetchModal } from "@/components/metadata";
import { useBook } from "@/hooks/useBook";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";
import type { BookUpdate } from "@/types/book";
import { formatFileSize } from "@/utils/format";
import styles from "./BookEditModal.module.scss";

export interface BookEditModalProps {
  /** Book ID to edit. */
  bookId: number | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
}

/**
 * Book edit modal component.
 *
 * Displays a comprehensive form for editing book metadata in a modal overlay.
 * Follows SRP by delegating to specialized components.
 * Uses IOC via hooks and components.
 */
export function BookEditModal({ bookId, onClose }: BookEditModalProps) {
  const { book, isLoading, error, updateBook, isUpdating, updateError } =
    useBook({
      bookId: bookId || 0,
      enabled: bookId !== null,
      full: true,
    });

  // Form state
  const [formData, setFormData] = useState<BookUpdate>({});
  const [hasChanges, setHasChanges] = useState(false);
  const [showMetadataModal, setShowMetadataModal] = useState(false);

  // Handle keyboard navigation
  useKeyboardNavigation({
    onEscape: onClose,
    enabled: !isLoading && !!book && bookId !== null,
  });

  // Prevent body scroll when modal is open
  useModal(bookId !== null);

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
        language_code: book.language || null,
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

      const updated = await updateBook(cleanedPayload);
      if (updated) {
        setHasChanges(false);
        onClose();
      }
    },
    [bookId, formData, updateBook, onClose],
  );

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  const handleModalClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      e.stopPropagation();
    },
    [],
  );

  const handleOverlayKeyDown = useCallback(() => {
    // Keyboard navigation is handled by useKeyboardNavigation hook
  }, []);

  if (!bookId) {
    return null;
  }

  if (isLoading) {
    return (
      /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
      <div
        className={styles.modalOverlay}
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={styles.modal}
          role="dialog"
          aria-modal="true"
          aria-label="Editing book info"
          onMouseDown={handleModalClick}
        >
          <div className={styles.loading}>Loading book data...</div>
        </div>
      </div>
    );
  }

  if (error || !book) {
    return (
      /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
      <div
        className={styles.modalOverlay}
        onClick={handleOverlayClick}
        onKeyDown={handleOverlayKeyDown}
        role="presentation"
      >
        <div
          className={styles.modal}
          role="dialog"
          aria-modal="true"
          aria-label="Editing book info"
          onMouseDown={handleModalClick}
        >
          <div className={styles.error}>
            {error || "Book not found"}
            <Button onClick={onClose} variant="secondary" size="medium">
              Close
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const authorsText =
    book.authors.length > 0 ? book.authors.join(", ") : "Unknown Author";
  const modalTitle = `Editing book info - ${book.title} by ${authorsText}`;

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className={styles.modalOverlay}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-label={modalTitle}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className={styles.closeButton}
          aria-label="Close"
        >
          ×
        </button>

        <div className={styles.header}>
          <h2 className={styles.title}>
            Editing {formData.title || book.title || "Untitled"}
          </h2>
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

        {showMetadataModal && (
          <MetadataFetchModal
            book={book}
            onClose={() => setShowMetadataModal(false)}
          />
        )}

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.content}>
            {/* Left Sidebar - Cover */}
            <div className={styles.leftSidebar}>
              <div className={styles.coverContainer}>
                {book.thumbnail_url ? (
                  <div className={styles.coverWrapper}>
                    <Image
                      src={book.thumbnail_url}
                      alt={`Cover for ${book.title}`}
                      width={200}
                      height={300}
                      className={styles.cover}
                      unoptimized
                    />
                    <div className={styles.coverOverlay}>
                      <button
                        type="button"
                        className={styles.coverActionButton}
                        aria-label="View cover"
                        title="View cover"
                      >
                        <span
                          className="pi pi-arrow-up-right-and-arrow-down-left-from-center"
                          aria-hidden="true"
                        />
                      </button>
                      <button
                        type="button"
                        className={styles.coverActionButton}
                        aria-label="Delete cover"
                        title="Delete cover"
                      >
                        <span className="pi pi-trash" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className={styles.coverPlaceholder}>
                    <span>No Cover</span>
                  </div>
                )}
                <div className={styles.coverActions}>
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    className={styles.coverAction}
                  >
                    <span className="pi pi-image" aria-hidden="true" />
                    Select cover
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    className={styles.coverAction}
                  >
                    <span className="pi pi-download" aria-hidden="true" />
                    Download cover
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    className={styles.coverAction}
                  >
                    <span className="pi pi-sparkles" aria-hidden="true" />
                    Generate cover
                  </Button>
                </div>
              </div>

              {/* Formats Section */}
              <div className={styles.formatsSection}>
                <h3 className={styles.formatsTitle}>Formats</h3>
                {book.formats && book.formats.length > 0 ? (
                  <div className={styles.formatsList}>
                    {book.formats.map((file) => (
                      <div
                        key={`${file.format}-${file.size}`}
                        className={styles.formatItem}
                      >
                        <div className={styles.formatIcon}>
                          {file.format.toUpperCase()}
                        </div>
                        <div className={styles.formatInfo}>
                          <span className={styles.formatName}>
                            {file.format.toUpperCase()}
                          </span>
                          <span className={styles.formatSize}>
                            {formatFileSize(file.size)}
                          </span>
                        </div>
                        <div className={styles.formatActions}>
                          <button
                            type="button"
                            className={styles.formatActionButton}
                            aria-label={`Info for ${file.format.toUpperCase()}`}
                            title={`Info for ${file.format.toUpperCase()}`}
                          >
                            <span
                              className="pi pi-info-circle"
                              aria-hidden="true"
                            />
                          </button>
                          <button
                            type="button"
                            className={styles.formatActionButton}
                            aria-label={`Copy ${file.format.toUpperCase()}`}
                            title={`Copy ${file.format.toUpperCase()}`}
                          >
                            <span className="pi pi-copy" aria-hidden="true" />
                          </button>
                          <button
                            type="button"
                            className={styles.formatActionButton}
                            aria-label={`Delete ${file.format.toUpperCase()}`}
                            title={`Delete ${file.format.toUpperCase()}`}
                          >
                            <span className="pi pi-trash" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className={styles.noFormats}>No formats available</div>
                )}
                <div className={styles.formatButtons}>
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    className={styles.formatAction}
                  >
                    <span className="pi pi-plus" aria-hidden="true" />
                    Add new format
                  </Button>
                  <Button
                    type="button"
                    variant="ghost"
                    size="small"
                    className={styles.formatAction}
                  >
                    <span className="pi pi-refresh" aria-hidden="true" />
                    Convert
                  </Button>
                </div>
              </div>
            </div>

            {/* Main Content - Three Column Grid */}
            <div className={styles.mainContent}>
              <div className={styles.formGrid}>
                {/* Row 1: Title and Title Sort */}
                <div className={styles.spanningRow}>
                  <div className={styles.fieldRow}>
                    <TextInput
                      id="title"
                      label="Title"
                      value={formData.title || ""}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                        handleFieldChange("title", e.target.value)
                      }
                      required
                      className={styles.field}
                    />
                    <button
                      type="button"
                      className={styles.arrowButton}
                      aria-label="Copy to title sort"
                      title="Copy to title sort"
                    >
                      →
                    </button>
                  </div>
                  <TextInput
                    id="title_sort"
                    label="Title Sort"
                    value={book.title || ""}
                    disabled
                    className={styles.field}
                  />
                </div>

                {/* Row 2: Author(s) and Author(s) Sort */}
                <div className={styles.spanningRow}>
                  <div className={styles.fieldRow}>
                    <MultiTextInput
                      id="authors"
                      label="Author (comma or Enter to add)"
                      values={formData.author_names || []}
                      onChange={(authors) =>
                        handleFieldChange("author_names", authors)
                      }
                      placeholder="Add author names (press Enter or comma)"
                      filterType="author"
                    />
                    <button
                      type="button"
                      className={styles.arrowButton}
                      aria-label="Copy to author sort"
                      title="Copy to author sort"
                    >
                      →
                    </button>
                  </div>
                  <TextInput
                    id="author_sort"
                    label="Author(s)"
                    value={book.author_sort || ""}
                    disabled
                    className={styles.field}
                  />
                </div>

                {/* Row 3: Series, Number, Rating */}
                <div className={styles.seriesRow}>
                  <AutocompleteTextInput
                    id="series_name"
                    label="Series"
                    value={formData.series_name || ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleFieldChange(
                        "series_name",
                        (e.target as HTMLInputElement).value || null,
                      )
                    }
                    placeholder="Enter series name"
                    filterType="series"
                    className={styles.seriesField}
                  />
                  <NumberInput
                    id="series_index"
                    label="Number"
                    value={formData.series_index ?? ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleFieldChange(
                        "series_index",
                        e.target.value ? parseFloat(e.target.value) : null,
                      )
                    }
                    step={0.1}
                    min={0}
                    className={styles.numberField}
                  />
                  <div className={styles.ratingField}>
                    <RatingInput
                      id="rating"
                      label="Rating"
                      value={formData.rating_value ?? null}
                      onChange={(rating) =>
                        handleFieldChange("rating_value", rating)
                      }
                    />
                  </div>
                </div>

                {/* Row 4: Tags and Manage Tags button */}
                <div className={styles.spanningRow}>
                  <TagInput
                    id="tags"
                    label="Tags"
                    tags={formData.tag_names || []}
                    onChange={(tags) => handleFieldChange("tag_names", tags)}
                    placeholder="Add tags (press Enter or comma)"
                    filterType="genre"
                  />
                  <div className={styles.tagActionsColumn}>
                    <Button
                      type="button"
                      variant="ghost"
                      size="small"
                      onClick={() => {
                        // TODO: Implement manage tags
                      }}
                    >
                      Manage tags
                    </Button>
                  </div>
                </div>

                {/* Row 5: Identifiers and Languages */}
                <div className={styles.spanningRow}>
                  <IdentifierInput
                    id="identifiers"
                    label="Identifiers"
                    identifiers={formData.identifiers || []}
                    onChange={(identifiers) =>
                      handleFieldChange("identifiers", identifiers)
                    }
                  />
                  <TagInput
                    id="languages"
                    label="Languages"
                    tags={
                      formData.language_code ? [formData.language_code] : []
                    }
                    onChange={(languages) =>
                      handleFieldChange(
                        "language_code",
                        languages.length > 0 ? languages[0] : null,
                      )
                    }
                    placeholder="Add language code"
                  />
                </div>

                {/* Row 6: Publisher and Publish date */}
                <div className={styles.spanningRow}>
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
                  <DateInput
                    id="pubdate"
                    label="Publish date"
                    value={formData.pubdate || ""}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      handleFieldChange("pubdate", e.target.value || null)
                    }
                  />
                </div>
              </div>

              {/* Full-width Description */}
              <div className={styles.descriptionSection}>
                <TextArea
                  id="description"
                  label="Description"
                  value={formData.description || ""}
                  onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) =>
                    handleFieldChange("description", e.target.value || null)
                  }
                  placeholder="Enter book description..."
                  rows={6}
                />
              </div>
            </div>
          </div>

          <div className={styles.footer}>
            {updateError && (
              <div className={styles.errorBanner} role="alert">
                {updateError}
              </div>
            )}
            <div className={styles.footerActions}>
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={onClose}
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
                Save info
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
