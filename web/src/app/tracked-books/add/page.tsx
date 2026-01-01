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

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import {
  FaBarcode,
  FaBook,
  FaCheck,
  FaCheckCircle,
  FaGlobe,
  FaPlus,
} from "react-icons/fa";
import { PageLayout } from "@/components/layout/PageLayout";
import { SearchInput } from "@/components/library/widgets/SearchInput";
import { MetadataSearchProgress } from "@/components/metadata/MetadataSearchProgress";
import { AddBookModal } from "@/components/tracked-books/AddBookModal";
import {
  type MetadataRecord,
  useMetadataSearchStream,
} from "@/hooks/useMetadataSearchStream";
import { trackedBookService } from "@/services/trackedBookService";
import type {
  MetadataSearchResult,
  MonitorMode,
  TrackedBook,
} from "@/types/trackedBook";

// Helper to convert MetadataRecord to MetadataSearchResult
function toMetadataSearchResult(record: MetadataRecord): MetadataSearchResult {
  return {
    id: String(record.external_id),
    title: record.title,
    author: record.authors.join(", "),
    authors: record.authors,
    isbn: record.identifiers?.isbn,
    identifiers: record.identifiers,
    year: record.published_date?.substring(0, 4),
    published_date: record.published_date || undefined,
    cover_url: record.cover_url || undefined,
    description: record.description || undefined,
    provider: record.source_id,
    source_id: record.source_id,
    external_id: String(record.external_id),
    score: record.rating || undefined, // Assuming rating matches score scale or is undefined
    tags: record.tags,
  };
}

function AddBookContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialQuery = searchParams.get("q") || "";
  const [searchTerm, setSearchTerm] = useState(initialQuery);
  const [selectedBook, setSelectedBook] = useState<MetadataSearchResult | null>(
    null,
  );
  const [isAdding, setIsAdding] = useState(false);
  const [trackedBooks, setTrackedBooks] = useState<TrackedBook[]>([]);

  // Use the streaming search hook
  const { state, startSearch } = useMetadataSearchStream({
    query: searchTerm,
    providerIds: ["google", "hardcover"],
    enabled: false, // Manual trigger
  });

  // Fetch tracked books on mount
  useEffect(() => {
    trackedBookService.getAll().then(setTrackedBooks).catch(console.error);
  }, []);

  // Create a map of composite keys to tracked book IDs for quick lookup
  // Composite key format: `${source_id}:${external_id}`
  const trackedBookMap = useMemo(() => {
    const map = new Map<string, number>();
    if (!Array.isArray(trackedBooks)) return map;
    for (const book of trackedBooks) {
      if (book.metadata_source_id && book.metadata_external_id) {
        map.set(
          `${book.metadata_source_id}:${book.metadata_external_id}`,
          book.id,
        );
      }
    }
    return map;
  }, [trackedBooks]);

  const getTrackedBookId = (
    book: MetadataSearchResult & { source_id?: string; external_id?: string },
  ) => {
    const sourceId = book.source_id || book.provider;
    const externalId = book.id || book.external_id;
    if (!sourceId || !externalId) return undefined;
    return trackedBookMap.get(`${sourceId}:${externalId}`);
  };

  const handleSearch = useCallback(
    (term: string) => {
      if (!term.trim()) return;
      setSearchTerm(term);
      startSearch(term);
    },
    [startSearch],
  );

  // Effect to trigger search when initialQuery is available
  useEffect(() => {
    if (
      initialQuery &&
      !state.isSearching &&
      state.results.length === 0 &&
      !state.error
    ) {
      handleSearch(initialQuery);
    }
  }, [
    initialQuery,
    handleSearch,
    state.error,
    state.isSearching,
    state.results.length,
  ]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleAddClick = (book: MetadataSearchResult) => {
    setSelectedBook(book);
  };

  const handleModalAdd = async (
    book: MetadataSearchResult,
    settings: {
      libraryId?: number;
      monitor: MonitorMode;
      monitorValue: string;
      preferredFormats: string[];
      tags: string[];
    },
  ) => {
    setIsAdding(true);

    // Transform the book object to match backend expectations
    const payload: Partial<TrackedBook> = {
      title: book.title,
      // Convert array of authors to string if necessary
      author:
        settings.monitor === "author" && settings.monitorValue
          ? settings.monitorValue
          : book.author,
      metadata_source_id: book.provider,
      metadata_external_id: book.id,
      isbn: book.isbn,
      cover_url: book.cover_url,
      description: book.description,
      publisher: "", // Default empty string as it's not in MetadataSearchResult
      published_date: "", // Default empty string as it's not in MetadataSearchResult
      rating: book.score,

      // Settings from modal
      library_id: settings.libraryId,
      auto_search_enabled: true, // Always enable search for now
      auto_download_enabled: false, // Default to false for now until we implement download logic
      monitor_mode: settings.monitor,
      preferred_formats:
        settings.preferredFormats.length > 0
          ? settings.preferredFormats
          : undefined,
      tags: settings.tags,
    };

    try {
      await trackedBookService.add(payload);
      // Refresh tracked books list
      const updatedBooks = await trackedBookService.getAll();
      setTrackedBooks(updatedBooks);
      setSelectedBook(null); // Close modal on success
    } catch (error) {
      console.error("Failed to add book:", error);
      alert("Failed to add book to tracked list");
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <div className="flex h-full w-full flex-col p-4 md:p-8">
      {selectedBook && (
        <AddBookModal
          isOpen={true}
          book={selectedBook}
          onClose={() => setSelectedBook(null)}
          onAdd={handleModalAdd}
          isAdding={isAdding}
        />
      )}
      <div className="mb-6">
        <h1 className="mb-2 font-bold text-2xl text-text-a0">Add New Book</h1>
        <p className="text-sm text-text-a30">
          Search for books to add to your watch list
        </p>
      </div>

      <div className="mb-8">
        <SearchInput
          value={searchTerm}
          onChange={setSearchTerm}
          onSubmit={handleSearch}
          placeholder="Search for books by title or author..."
        />
      </div>

      {state.totalProviders > 0 && <MetadataSearchProgress state={state} />}

      {state.error && (
        <div className="mb-4 rounded-md border border-danger-a20 bg-danger-a20/10 p-4 text-danger-a0 text-sm">
          {state.error}
        </div>
      )}

      {state.isSearching && state.results.length === 0 ? (
        <div className="flex justify-center py-12">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-a0 border-t-transparent" />
        </div>
      ) : (
        <div className="mt-4 grid gap-4">
          {!state.isSearching &&
          state.totalProviders > 0 &&
          state.results.length === 0 ? (
            <div className="py-12 text-center text-text-a30">
              No results found for "{searchTerm}"
            </div>
          ) : (
            state.results.map((record: MetadataRecord) => {
              const book = toMetadataSearchResult(record);
              const trackedId = getTrackedBookId(book);
              const alreadyTracked = trackedId !== undefined;

              return (
                <div
                  key={book.id || book.external_id}
                  className="flex flex-col gap-4 rounded-md bg-surface-tonal-a10 p-4 text-text-a0 shadow-md md:flex-row"
                >
                  {/* Poster Section */}
                  <div className="flex w-full flex-shrink-0 flex-col md:w-[140px]">
                    {/* biome-ignore lint/a11y/useSemanticElements: using div for layout reasons (aspect ratio) but behaving like a button */}
                    <div
                      className="relative aspect-[2/3] w-full cursor-pointer overflow-hidden rounded-t-sm"
                      onClick={() =>
                        alreadyTracked
                          ? router.push(`/tracked-books/${trackedId}`)
                          : handleAddClick(book)
                      }
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          if (alreadyTracked) {
                            router.push(`/tracked-books/${trackedId}`);
                          } else {
                            handleAddClick(book);
                          }
                        }
                      }}
                      role="button"
                      tabIndex={0}
                      aria-label={
                        alreadyTracked
                          ? `View ${book.title}`
                          : `Select ${book.title}`
                      }
                    >
                      {book.cover_url ? (
                        <img
                          src={book.cover_url}
                          alt={book.title}
                          className="h-full w-full object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-surface-a30">
                          <FaBook className="h-10 w-10 text-text-a40" />
                        </div>
                      )}
                    </div>
                    {alreadyTracked ? (
                      <button
                        type="button"
                        onClick={() =>
                          router.push(`/tracked-books/${trackedId}`)
                        }
                        className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-b-sm border border-surface-tonal-a30 border-t-0 bg-surface-tonal-a20 py-1.5 font-bold text-text-a30 text-xs uppercase tracking-wider transition-colors hover:bg-surface-tonal-a30 hover:text-text-a10"
                      >
                        <FaCheck className="text-[10px]" />
                        <span>Tracked</span>
                      </button>
                    ) : (
                      <button
                        type="button"
                        onClick={() => handleAddClick(book)}
                        className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-b-sm bg-primary-a0 py-1.5 font-bold text-surface-a0 text-xs uppercase tracking-wider transition-colors hover:bg-primary-a30"
                      >
                        <FaPlus className="text-[10px]" />
                        <span>Track</span>
                      </button>
                    )}
                  </div>

                  {/* Content Section */}
                  <div className="flex min-w-0 flex-1 flex-col gap-2">
                    {/* Header: Title + Year + Checkmark */}
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                        <h3 className="font-bold text-2xl text-text-a0 leading-tight">
                          {book.title}
                        </h3>
                        {book.published_date && (
                          <span className="font-normal text-lg text-text-a30">
                            ({book.published_date.substring(0, 4)})
                          </span>
                        )}
                        <FaCheckCircle
                          className={`h-5 w-5 ${alreadyTracked ? "text-success-a10" : "text-surface-a30"}`}
                          title={alreadyTracked ? "Tracked" : "Not tracked"}
                        />
                      </div>
                    </div>

                    {/* Badges Row */}
                    <div className="flex flex-wrap items-center gap-2 font-medium text-xs">
                      {/* Score */}
                      {book.score !== undefined && (
                        <span
                          className={`inline-flex items-center gap-1 rounded border border-surface-a20 bg-surface-tonal-a0 px-1.5 py-0.5 ${book.score >= 70 ? "text-success-a10" : "text-warning-a10"}`}
                        >
                          <span className="font-bold">{book.score}%</span>
                        </span>
                      )}

                      {/* Provider */}
                      <span className="inline-flex items-center gap-1 rounded border border-surface-a20 bg-surface-tonal-a0 px-1.5 py-0.5 text-text-a20 capitalize">
                        <FaGlobe className="text-[10px] text-text-a30" />
                        {book.provider}
                      </span>

                      {/* ISBN */}
                      {book.isbn && (
                        <span className="inline-flex items-center gap-1 rounded border border-surface-a20 bg-surface-tonal-a0 px-1.5 py-0.5 text-text-a20">
                          <FaBarcode className="text-[10px] text-text-a30" />
                          {book.isbn}
                        </span>
                      )}

                      {/* Language */}
                      <span className="inline-flex items-center gap-1 rounded border border-surface-a20 bg-surface-tonal-a0 px-1.5 py-0.5 text-text-a20">
                        English
                      </span>

                      {/* Author Badge (mimicking Studio) */}
                      <span className="inline-flex items-center gap-1 rounded border border-surface-a20 bg-surface-tonal-a0 px-1.5 py-0.5 text-text-a20">
                        {book.author}
                      </span>
                    </div>

                    {/* Description */}
                    <p className="mt-2 line-clamp-4 text-sm text-text-a30 leading-relaxed md:line-clamp-6">
                      {book.description ||
                        "No description available for this book."}
                    </p>
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}
    </div>
  );
}

export default function AddBookPage() {
  return (
    <PageLayout>
      <Suspense fallback={<div className="p-8">Loading search...</div>}>
        <AddBookContent />
      </Suspense>
    </PageLayout>
  );
}
