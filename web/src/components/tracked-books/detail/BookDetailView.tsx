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

import { useState } from "react";
import { FaHistory } from "react-icons/fa";
import { InteractiveSearchModal } from "@/components/pvr/InteractiveSearchModal";
import { cn } from "@/libs/utils";
import type { TrackedBook } from "@/types/trackedBook";
import { extractYear } from "@/utils/dateFormatters";
import { BookFiles } from "./BookFiles";
import { BookHeader } from "./BookHeader";
import { InfoCard } from "./InfoCard";
import { InfoRow } from "./InfoRow";
import { StatusBadge } from "./StatusBadge";

interface BookDetailViewProps {
  book: TrackedBook;
}

type Tab = "overview" | "history";

export function BookDetailView({ book }: BookDetailViewProps) {
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);

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
        book={book}
        onSearchClick={() => setIsSearchModalOpen(true)}
      />

      <BookFiles files={book.files} />

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
                    value={<StatusBadge status={book.status} />}
                  />
                  <InfoRow
                    label="Monitor"
                    value={
                      <span className="capitalize">
                        {book.monitor_mode?.replace("_", " ")}
                      </span>
                    }
                  />
                  <InfoRow
                    label="Formats"
                    value={book.preferred_formats?.join(", ") || "Any"}
                  />
                </div>
              </InfoCard>

              <InfoCard title="Metadata">
                <div className="flex flex-col gap-2 text-sm">
                  <InfoRow label="Author" value={book.author} />
                  <InfoRow label="Publisher" value={book.publisher || "-"} />
                  <InfoRow
                    label="Published"
                    value={book.published_date || "-"}
                  />
                  <InfoRow label="ISBN" value={book.isbn || "-"} />
                  <InfoRow
                    label="Goodreads ID"
                    value={book.metadata_external_id || "-"}
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
        trackedBookId={book.id}
        bookTitle={book.title}
        bookYear={
          book.published_date ? extractYear(book.published_date) : undefined
        }
      />
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
