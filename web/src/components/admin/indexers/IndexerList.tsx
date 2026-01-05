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

import { FaSpinner } from "react-icons/fa";
import type { Indexer } from "@/types/indexer";
import { IndexerCard } from "./IndexerCard";

interface IndexerListProps {
  indexers: Indexer[];
  isLoading: boolean;
  onEdit: (indexer: Indexer) => void;
  onRefresh: () => void;
}

export function IndexerList({
  indexers,
  isLoading,
  onEdit,
  onRefresh,
}: IndexerListProps) {
  return (
    <>
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-text-a30">
          <FaSpinner className="animate-spin" />
          Loading...
        </div>
      )}

      {indexers.length === 0 && !isLoading ? (
        <div className="text-text-a30 italic">No indexers configured.</div>
      ) : (
        <div className="flex flex-col gap-4">
          {indexers.map((indexer) => (
            <IndexerCard
              key={indexer.id}
              indexer={indexer}
              onEdit={onEdit}
              onRefresh={onRefresh}
            />
          ))}
        </div>
      )}
    </>
  );
}
