"use client";

import {
  FaCheckCircle,
  FaCog,
  FaDownload,
  FaExclamationCircle,
  FaTrash,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import {
  type DownloadClient,
  DownloadClientStatus,
} from "@/types/downloadClient";

interface DownloadClientCardProps {
  client: DownloadClient;
  onEdit: (client: DownloadClient) => void;
  onDelete: (client: DownloadClient) => void;
  onViewItems?: (client: DownloadClient) => void;
}

export function DownloadClientCard({
  client,
  onEdit,
  onDelete,
  onViewItems,
}: DownloadClientCardProps) {
  return (
    <div className="flex items-center justify-between rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a10)] p-4">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-text-a0">{client.name}</span>
          <StatusBadge status={client.status} />
          {!client.enabled && (
            <span className="rounded bg-[var(--color-surface-a20)] px-2 py-0.5 text-text-a30 text-xs">
              Disabled
            </span>
          )}
        </div>
        <div className="text-sm text-text-a30">
          <span className="capitalize">{client.client_type}</span> •{" "}
          <span>
            {client.host}:{client.port}
          </span>
        </div>
        {client.error_message && (
          <div className="mt-1 text-[var(--color-danger-a0)] text-xs">
            {client.error_message}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        {onViewItems && (
          <Button
            variant="ghost"
            size="small"
            onClick={() => onViewItems(client)}
            title="View Active Downloads"
          >
            <FaDownload className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="small"
          onClick={() => onEdit(client)}
          title="Edit"
        >
          <FaCog className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="small"
          onClick={() => onDelete(client)}
          className="text-[var(--color-danger-a0)] hover:text-[var(--color-danger-a10)]"
          title="Delete"
        >
          <FaTrash className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: DownloadClientStatus }) {
  if (status === DownloadClientStatus.HEALTHY) {
    return (
      <span className="text-[var(--color-success-a0)]" title="Healthy">
        <FaCheckCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === DownloadClientStatus.DEGRADED) {
    return (
      <span className="text-[var(--color-warning-a0)]" title="Degraded">
        <FaExclamationCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === DownloadClientStatus.UNHEALTHY) {
    return (
      <span className="text-[var(--color-danger-a0)]" title="Unhealthy">
        <FaExclamationCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === DownloadClientStatus.DISABLED) {
    return (
      <span className="text-text-a30" title="Disabled">
        <FaExclamationCircle className="h-4 w-4" />
      </span>
    );
  }
  return (
    <span className="text-text-a30" title="Unknown">
      <FaExclamationCircle className="h-4 w-4" />
    </span>
  );
}
