"use client";

import { FaSpinner } from "react-icons/fa";
import type { Indexer } from "@/types/indexer";
import { IndexerCard } from "./IndexerCard";

interface IndexerListProps {
  indexers: Indexer[];
  isLoading: boolean;
  onEdit: (indexer: Indexer) => void;
  onDelete: (indexer: Indexer) => void;
}

export function IndexerList({
  indexers,
  isLoading,
  onEdit,
  onDelete,
}: IndexerListProps) {
  return (
    <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-text-a0 text-xl">Indexers</h2>
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-text-a30">
            <FaSpinner className="animate-spin" />
            Loading...
          </div>
        )}
      </div>

      {indexers.length === 0 && !isLoading ? (
        <div className="text-text-a30 italic">No indexers configured.</div>
      ) : (
        <div className="flex flex-col gap-4">
          {indexers.map((indexer) => (
            <IndexerCard
              key={indexer.id}
              indexer={indexer}
              onEdit={onEdit}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}
