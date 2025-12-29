"use client";

import {
  FaCheckCircle,
  FaCog,
  FaExclamationCircle,
  FaTrash,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { type Indexer, IndexerStatus } from "@/types/indexer";

interface IndexerCardProps {
  indexer: Indexer;
  onEdit: (indexer: Indexer) => void;
  onDelete: (indexer: Indexer) => void;
}

export function IndexerCard({ indexer, onEdit, onDelete }: IndexerCardProps) {
  return (
    <div className="flex items-center justify-between rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a10)] p-4">
      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-text-a0">{indexer.name}</span>
          <StatusBadge status={indexer.status} />
          {!indexer.enabled && (
            <span className="rounded bg-[var(--color-surface-a20)] px-2 py-0.5 text-text-a30 text-xs">
              Disabled
            </span>
          )}
        </div>
        <div className="text-sm text-text-a30">
          <span className="capitalize">{indexer.indexer_type}</span> •{" "}
          <span className="capitalize">{indexer.protocol}</span>
        </div>
        {indexer.error_message && (
          <div className="mt-1 text-[var(--color-danger-a0)] text-xs">
            {indexer.error_message}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="small" onClick={() => onEdit(indexer)}>
          <FaCog className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="small"
          onClick={() => onDelete(indexer)}
          className="text-[var(--color-danger-a0)] hover:text-[var(--color-danger-a10)]"
        >
          <FaTrash className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}

function StatusBadge({ status }: { status: IndexerStatus }) {
  if (status === IndexerStatus.HEALTHY) {
    return (
      <span className="text-[var(--color-success-a0)]" title="Healthy">
        <FaCheckCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === IndexerStatus.DEGRADED) {
    return (
      <span className="text-[var(--color-warning-a0)]" title="Degraded">
        <FaExclamationCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === IndexerStatus.UNHEALTHY) {
    return (
      <span className="text-[var(--color-danger-a0)]" title="Unhealthy">
        <FaExclamationCircle className="h-4 w-4" />
      </span>
    );
  }
  if (status === IndexerStatus.DISABLED) {
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
