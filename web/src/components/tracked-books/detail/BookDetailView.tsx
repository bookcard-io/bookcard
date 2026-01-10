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
import { useEffect, useState } from "react";
import { FaHistory } from "react-icons/fa";
import { InteractiveSearchModal } from "@/components/pvr/InteractiveSearchModal";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { cn } from "@/libs/utils";
import type { TrackedBook } from "@/types/trackedBook";
import { extractYear } from "@/utils/dateFormatters";
import { BookFiles } from "./BookFiles";
import { BookHeader } from "./BookHeader";
import { InfoCard } from "./InfoCard";
import { InfoRow } from "./InfoRow";
import { StatusBadge } from "./StatusBadge";
import { TrackedBookEditModal } from "./TrackedBookEditModal";

interface BookDetailViewProps {
  book: TrackedBook;
}

type Tab = "overview" | "history";

export function BookDetailView({ book }: BookDetailViewProps) {
  const router = useRouter();
  const { showDanger } = useGlobalMessages();
  const [currentBook, setCurrentBook] = useState<TrackedBook>(book);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [_isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    setCurrentBook(book);
  }, [book]);

  const handleDelete = async () => {
    if (
      !confirm(
        "Are you sure you want to delete this book from tracking? This will remove all download history and files associated with the tracked record, but will NOT remove the book from your Calibre library.",
      )
    ) {
      return;
    }

    try {
      setIsDeleting(true);
      const response = await fetch(`/api/tracked-books/${book.id}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error("Failed to delete tracked book");
      }

      router.push("/tracked-books");
      router.refresh();
    } catch (error) {
      console.error("Error deleting book:", error);
      showDanger("Failed to delete book");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="relative flex min-h-full flex-col bg-surface-a0">
      {/* Background blurred image */}
      <div
        className="absolute inset-0 z-0 opacity-10 blur-3xl"
        style={{
          backgroundImage: `url(${book.cover_url})`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      <BookHeader
        book={currentBook}
        onSearchClick={() => setIsSearchModalOpen(true)}
        onEditClick={() => setIsEditModalOpen(true)}
        onDeleteClick={handleDelete}
      />

      <BookFiles files={currentBook.files} />

      {/* Tabs & Content */}
      <div className="flex flex-col">
        {/* Tab Headers */}
        <div className="flex gap-6 bg-surface-a0 px-4 md:px-8">
          <TabButton
            active={activeTab === "overview"}
            onClick={() => setActiveTab("overview")}
            label="Overview"
          />
          <TabButton
            active={activeTab === "history"}
            onClick={() => setActiveTab("history")}
            label="History"
          />
        </div>

        {/* Tab Content */}
        <div className="bg-surface-a0 p-4 md:p-8">
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
              <InfoCard title="Monitoring">
                <div className="flex flex-col gap-2 text-sm">
                  <InfoRow
                    label="Status"
                    value={<StatusBadge status={currentBook.status} />}
                  />
                  <InfoRow
                    label="Monitor"
                    value={
                      <span className="capitalize">
                        {currentBook.monitor_mode?.replace("_", " ")}
                      </span>
                    }
                  />
                  <InfoRow
                    label="Formats"
                    value={currentBook.preferred_formats?.join(", ") || "Any"}
                  />
                </div>
              </InfoCard>

              <InfoCard title="Metadata">
                <div className="flex flex-col gap-2 text-sm">
                  <InfoRow label="Author" value={currentBook.author} />
                  <InfoRow
                    label="Publisher"
                    value={currentBook.publisher || "-"}
                  />
                  <InfoRow
                    label="Published"
                    value={currentBook.published_date || "-"}
                  />
                  <InfoRow label="ISBN" value={currentBook.isbn || "-"} />
                  <InfoRow
                    label="Goodreads ID"
                    value={currentBook.metadata_external_id || "-"}
                  />
                </div>
              </InfoCard>
            </div>
          )}

          {activeTab === "history" && (
            <div className="flex flex-col items-center justify-center py-12 text-text-a30">
              <FaHistory className="mb-4 text-4xl opacity-20" />
              <p>No history available.</p>
            </div>
          )}
        </div>
      </div>

      <InteractiveSearchModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
        trackedBookId={currentBook.id}
        bookTitle={currentBook.title}
        bookYear={
          currentBook.published_date
            ? extractYear(currentBook.published_date)
            : undefined
        }
      />

      {isEditModalOpen && (
        <TrackedBookEditModal
          book={currentBook}
          onClose={() => setIsEditModalOpen(false)}
          onBookSaved={(updated) => {
            setCurrentBook(updated);
            setIsEditModalOpen(false);
          }}
        />
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  label,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative py-4 font-medium text-sm transition-colors",
        active ? "text-primary-a0" : "text-text-a30 hover:text-text-a10",
      )}
    >
      {label}
      {active && (
        <div className="absolute right-0 bottom-0 left-0 h-0.5 bg-primary-a0" />
      )}
    </button>
  );
}
