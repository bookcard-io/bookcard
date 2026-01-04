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
    <div className="flex flex-col gap-4">
      {isLoading && (
        <div className="flex items-center gap-2 text-sm text-text-a30">
          <FaSpinner className="animate-spin" />
          Loading...
        </div>
      )}

      {clients.length === 0 && !isLoading ? (
        <div className="text-text-a30 italic">
          No download clients configured.
        </div>
      ) : (
        clients.map((client) => (
          <DownloadClientCard
            key={client.id}
            client={client}
            onEdit={onEdit}
            onDelete={onDelete}
            onViewItems={onViewItems}
          />
        ))
      )}
    </div>
  );
}
