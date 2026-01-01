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
import {
  FaBook,
  FaCheck,
  FaDownload,
  FaGlobe,
  FaHistory,
  FaPenFancy,
  FaSearch,
  FaTag,
  FaTrash,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { PageLayout } from "@/components/layout/PageLayout";
import { Tooltip } from "@/components/layout/Tooltip";
import { cn } from "@/libs/utils";
import { trackedBookService } from "@/services/trackedBookService";
import type { TrackedBook } from "@/types/trackedBook";

interface TrackedBookDetailPageProps {
  params: Promise<{ id: string }>;
}

type Tab = "overview" | "history";

export default function TrackedBookDetailPage({
  params,
}: TrackedBookDetailPageProps) {
  const router = useRouter();
  const [book, setBook] = useState<TrackedBook | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("overview");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    void params.then(async (p) => {
      try {
        setIsLoading(true);
        const data = await trackedBookService.get(p.id);
        if (isMounted) setBook(data);
      } catch (err) {
        if (isMounted) setError("Failed to load book details");
        console.error(err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [params]);

  const handleBack = useCallback(() => {
    router.back();
  }, [router]);

  if (isLoading) {
    return (
      <PageLayout>
        <div className="flex h-full items-center justify-center text-text-a30">
          Loading book details...
        </div>
      </PageLayout>
    );
  }

  if (error || !book) {
    return (
      <PageLayout>
        <div className="flex h-full flex-col items-center justify-center gap-4 text-text-a30">
          <p>{error || "Book not found"}</p>
          <button
            type="button"
            onClick={handleBack}
            className="rounded-md bg-surface-tonal-a20 px-4 py-2 text-sm hover:bg-surface-tonal-a30"
          >
            Go Back
          </button>
        </div>
      </PageLayout>
    );
  }

  return (
    <PageLayout>
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

        {/* Banner / Header Area */}
        <div className="relative z-10 flex flex-col gap-6 border-surface-a20 p-6 md:flex-row md:p-8">
          {/* Poster */}
          <div className="z-10 w-[140px] flex-shrink-0 self-center md:self-start">
            <div className="aspect-[2/3] w-full overflow-hidden rounded-md shadow-lg">
              {book.cover_url ? (
                <img
                  src={book.cover_url}
                  alt={book.title}
                  className="h-full w-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center bg-surface-a30">
                  <FaBook className="h-12 w-12 text-text-a40" />
                </div>
              )}
            </div>
          </div>

          {/* Info Column */}
          <div className="z-10 flex min-w-0 flex-1 flex-col justify-between gap-4">
            <div>
              {/* Title & Year */}
              <div className="mb-1 flex flex-wrap items-baseline gap-x-3">
                <h1 className="font-bold text-3xl text-text-a0 md:text-4xl">
                  {book.title}
                </h1>
                {book.published_date && (
                  <span className="text-text-a30 text-xl">
                    {book.published_date.substring(0, 4)}
                  </span>
                )}
              </div>

              {/* Subtitle / Path / Details */}
              <div className="mb-4 flex flex-col gap-1 text-sm text-text-a30">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-text-a10">
                    {book.author}
                  </span>
                  {book.isbn && <span>• ISBN: {book.isbn}</span>}
                  {book.publisher && <span>• {book.publisher}</span>}
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs opacity-70">
                    /books/{book.author}/{book.title}
                  </span>
                </div>
              </div>

              {/* Status, Badges & Tags */}
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <StatusBadge status={book.status} />
                <span className="flex items-center gap-1 rounded-md border border-surface-a20 bg-surface-a0 px-2 py-1 text-text-a20 text-xs uppercase tracking-wide">
                  <FaGlobe className="text-text-a40" />
                  {book.metadata_source_id}
                </span>
                {book.rating && (
                  <span
                    className={cn(
                      "flex items-center gap-1 rounded-md border border-surface-a20 bg-surface-a0 px-2 py-1 font-bold text-xs",
                      book.rating >= 80
                        ? "text-success-a10"
                        : "text-warning-a10",
                    )}
                  >
                    {book.rating}%
                  </span>
                )}
                {book.tags?.map((tag) => (
                  <span
                    key={tag}
                    className="flex items-center gap-1 rounded-md bg-surface-a20 px-3 py-1 text-text-a20 text-xs transition-colors hover:bg-surface-a30"
                  >
                    <FaTag className="text-[10px] opacity-70" />
                    {tag}
                  </span>
                ))}
              </div>

              {/* Toolbar */}
              <div className="mt-6 flex flex-wrap items-center gap-4">
                <Button variant="primary" size="small">
                  <FaSearch />
                  Interactive Search
                </Button>

                <div className="flex items-center gap-2">
                  <Tooltip text="Edit">
                    <button
                      type="button"
                      className="flex h-10 w-10 items-center justify-center rounded-full text-text-a20 transition-colors hover:bg-surface-a20 hover:text-text-a0"
                    >
                      <FaPenFancy className="text-lg" />
                    </button>
                  </Tooltip>
                  <Tooltip text="Manual Import">
                    <button
                      type="button"
                      className="flex h-10 w-10 items-center justify-center rounded-full text-text-a20 transition-colors hover:bg-surface-a20 hover:text-text-a0"
                    >
                      <FaHistory className="text-lg" />
                    </button>
                  </Tooltip>
                  <Tooltip text="Delete">
                    <button
                      type="button"
                      className="flex h-10 w-10 items-center justify-center rounded-full text-text-a20 transition-colors hover:bg-surface-a20 hover:text-danger-a10"
                    >
                      <FaTrash className="text-lg" />
                    </button>
                  </Tooltip>
                </div>
              </div>
            </div>

            {/* Description */}
            <BookDescription description={book.description} />
          </div>
        </div>

        {/* Files Section */}
        <div className="flex flex-col gap-4 border-surface-a20 bg-surface-a0 p-6 md:px-8">
          <h2 className="border-surface-a20 border-b pb-2 font-bold text-text-a0 text-xl">
            Files
          </h2>
          <div className="overflow-hidden rounded-md border border-surface-a20 bg-surface-a0">
            {/* Header */}
            <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 bg-surface-tonal-a10 px-4 py-3 font-bold text-text-a30 text-xs uppercase tracking-wider md:grid-cols-[1fr_100px_100px_100px_80px]">
              <div className="flex items-center gap-1">Relative Path</div>
              <div className="text-right">Format</div>
              <div className="text-right">Size</div>
              <div className="text-right">Language</div>
              <div className="text-center">Actions</div>
            </div>

            {/* Empty State */}
            <div className="flex items-center justify-center bg-surface-a10/50 p-8 text-sm text-text-a30">
              No files to manage.
            </div>
          </div>
        </div>

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
      </div>
    </PageLayout>
  );
}

// Sub-components

function StatusBadge({ status }: { status: string }) {
  let colorClass = "bg-surface-a20 text-text-a20";
  let icon = null;

  switch (status) {
    case "completed":
      colorClass = "bg-success-a10/20 text-success-a10 border-success-a10/30";
      icon = <FaCheck className="text-[10px]" />;
      break;
    case "downloading":
      colorClass = "bg-info-a10/20 text-info-a10 border-info-a10/30";
      icon = <FaDownload className="text-[10px]" />;
      break;
    case "wanted":
      colorClass = "bg-danger-a10/20 text-danger-a10 border-danger-a10/30";
      icon = <FaSearch className="text-[10px]" />;
      break;
    case "searching":
      colorClass = "bg-warning-a10/20 text-warning-a10 border-warning-a10/30";
      icon = <FaSearch className="animate-pulse text-[10px]" />;
      break;
  }

  return (
    <span
      className={cn(
        "flex items-center gap-1.5 rounded-md border px-2.5 py-1 font-bold text-xs uppercase tracking-wider",
        colorClass,
      )}
    >
      {icon}
      {status}
    </span>
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

function InfoCard({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3">
      <h3 className="border-surface-a20 border-b pb-2 font-bold text-lg text-text-a0">
        {title}
      </h3>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex justify-between gap-4 py-1">
      <span className="text-text-a30">{label}</span>
      <span className="truncate text-right font-medium text-text-a10">
        {value}
      </span>
    </div>
  );
}

function BookDescription({ description }: { description?: string }) {
  const [expanded, setExpanded] = useState(false);
  const MAX_CHARS = 400;

  if (!description) return null;

  if (description.length <= MAX_CHARS) {
    return (
      <p className="max-w-4xl text-text-a20 leading-relaxed">{description}</p>
    );
  }

  return (
    <div className="max-w-4xl text-text-a20 leading-relaxed">
      {expanded ? (
        <>
          {description}
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="ml-2 cursor-pointer font-bold text-primary-a0 hover:text-primary-a10"
          >
            Less
          </button>
        </>
      ) : (
        <>
          {description.substring(0, MAX_CHARS)}...
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="ml-2 cursor-pointer font-bold text-primary-a0 hover:text-primary-a10"
          >
            More
          </button>
        </>
      )}
    </div>
  );
}
