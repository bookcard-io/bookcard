"use client";

import { FaSpinner } from "react-icons/fa";
import type { DownloadClient } from "@/types/downloadClient";
import { DownloadClientCard } from "./DownloadClientCard";

interface DownloadClientListProps {
  clients: DownloadClient[];
  isLoading: boolean;
  onEdit: (client: DownloadClient) => void;
  onDelete: (client: DownloadClient) => void;
  onViewItems?: (client: DownloadClient) => void;
}

export function DownloadClientList({
  clients,
  isLoading,
  onEdit,
  onDelete,
  onViewItems,
}: DownloadClientListProps) {
  return (
    <div className="rounded-lg border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] p-6">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-text-a0 text-xl">Download Clients</h2>
        {isLoading && (
          <div className="flex items-center gap-2 text-sm text-text-a30">
            <FaSpinner className="animate-spin" />
            Loading...
          </div>
        )}
      </div>

      {clients.length === 0 && !isLoading ? (
        <div className="text-text-a30 italic">
          No download clients configured.
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {clients.map((client) => (
            <DownloadClientCard
              key={client.id}
              client={client}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewItems={onViewItems}
            />
          ))}
        </div>
      )}
    </div>
  );
}
