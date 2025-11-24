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
import { PageLayout } from "@/components/layout/PageLayout";
import { RecentReadsList } from "@/components/reading/RecentReadsList";
import { useReadingSessions } from "@/hooks/useReadingSessions";
import type { ReadingSession } from "@/types/reading";

/**
 * Reading history page.
 *
 * Displays reading history with tabs for Recent Reads, All Sessions, and Reading Stats.
 * Follows SRP by delegating to specialized components.
 */
export default function ReadingHistoryPage() {
  const [activeTab, setActiveTab] = useState<"recent" | "sessions" | "stats">(
    "recent",
  );
  const { sessions, isLoading, error } = useReadingSessions({
    infiniteScroll: true,
    enabled: activeTab === "sessions",
  });

  return (
    <PageLayout>
      <div className="flex h-full flex-col gap-4 p-4 md:p-6">
        <div className="flex items-center justify-between">
          <h1 className="font-bold text-2xl text-text-a0">Reading History</h1>
        </div>

        <div className="flex gap-2 border-surface-a20 border-b">
          <button
            type="button"
            onClick={() => setActiveTab("recent")}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === "recent"
                ? "border-primary-a0 border-b-2 text-primary-a0"
                : "text-text-a40 hover:text-text-a0"
            }`}
          >
            Recent Reads
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("sessions")}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === "sessions"
                ? "border-primary-a0 border-b-2 text-primary-a0"
                : "text-text-a40 hover:text-text-a0"
            }`}
          >
            All Sessions
          </button>
          <button
            type="button"
            onClick={() => setActiveTab("stats")}
            className={`px-4 py-2 font-medium text-sm transition-colors ${
              activeTab === "stats"
                ? "border-primary-a0 border-b-2 text-primary-a0"
                : "text-text-a40 hover:text-text-a0"
            }`}
          >
            Reading Stats
          </button>
        </div>

        <div className="flex-1 overflow-auto">
          {activeTab === "recent" && (
            <div>
              <h2 className="mb-4 font-semibold text-lg text-text-a0">
                Recently Read Books
              </h2>
              <RecentReadsList limit={20} mode="grid" />
            </div>
          )}

          {activeTab === "sessions" && (
            <div>
              <h2 className="mb-4 font-semibold text-lg text-text-a0">
                All Reading Sessions
              </h2>
              {isLoading && (
                <div className="flex items-center justify-center p-8">
                  <span className="text-text-a40">Loading sessions...</span>
                </div>
              )}
              {error && (
                <div className="flex items-center justify-center p-8">
                  <span className="text-danger-a10">Error: {error}</span>
                </div>
              )}
              {!isLoading && !error && sessions.length === 0 && (
                <div className="flex items-center justify-center p-8">
                  <span className="text-text-a40">
                    No reading sessions yet.
                  </span>
                </div>
              )}
              {!isLoading && !error && sessions.length > 0 && (
                <div className="flex flex-col gap-2">
                  {sessions.map((session: ReadingSession) => (
                    <div
                      key={session.id}
                      className="flex items-center justify-between rounded-md border border-surface-a20 bg-surface-tonal-a0 p-3"
                    >
                      <div className="flex flex-col gap-1">
                        <span className="font-medium text-sm text-text-a0">
                          Book ID: {session.book_id} ({session.format})
                        </span>
                        <span className="text-text-a40 text-xs">
                          {new Date(session.started_at).toLocaleString()}
                          {session.ended_at &&
                            ` - ${new Date(session.ended_at).toLocaleString()}`}
                        </span>
                      </div>
                      <div className="text-text-a40 text-xs">
                        {session.duration
                          ? `${Math.round(session.duration / 60)} min`
                          : "Ongoing"}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {activeTab === "stats" && (
            <div>
              <h2 className="mb-4 font-semibold text-lg text-text-a0">
                Reading Statistics
              </h2>
              <div className="flex items-center justify-center p-8">
                <span className="text-text-a40">
                  Reading statistics coming soon.
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </PageLayout>
  );
}
