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
            title="View active downloads"
          >
            <FaDownload className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="small"
          onClick={() => onEdit(client)}
          title="Edit download client"
        >
          <FaCog className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="small"
          onClick={() => onDelete(client)}
          className="text-[var(--color-danger-a0)] hover:text-[var(--color-danger-a10)]"
          title="Delete download client"
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
