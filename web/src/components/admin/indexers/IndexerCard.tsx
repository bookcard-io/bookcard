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
import {
  FaCheckCircle,
  FaCog,
  FaExclamationCircle,
  FaNetworkWired,
  FaSpinner,
  FaTrash,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useIndexers } from "@/hooks/useIndexers";
import { type Indexer, IndexerStatus } from "@/types/indexer";

interface IndexerCardProps {
  indexer: Indexer;
  onEdit: (indexer: Indexer) => void;
  onRefresh: () => void;
}

export function IndexerCard({ indexer, onEdit, onRefresh }: IndexerCardProps) {
  const [isTesting, setIsTesting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { testConnection, deleteIndexer } = useIndexers(false);
  const { showSuccess, showDanger } = useGlobalMessages();

  const handleTest = async () => {
    setIsTesting(true);
    try {
      const result = await testConnection(indexer.id);
      if (result.success) {
        showSuccess(
          `Connection to "${indexer.name}" successful: ${result.message}`,
        );
        onRefresh();
      } else {
        showDanger(`Connection to "${indexer.name}" failed: ${result.message}`);
      }
    } catch (error) {
      showDanger(
        `Failed to test connection: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      );
    } finally {
      setIsTesting(false);
    }
  };

  const handleDelete = async () => {
    if (
      !confirm(`Are you sure you want to delete indexer "${indexer.name}"?`)
    ) {
      return;
    }
    setIsDeleting(true);
    try {
      await deleteIndexer(indexer.id);
      showSuccess(`Indexer "${indexer.name}" deleted successfully.`);
      onRefresh();
    } catch (error) {
      showDanger(
        `Failed to delete indexer: ${
          error instanceof Error ? error.message : "Unknown error"
        }`,
      );
    } finally {
      setIsDeleting(false);
    }
  };

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
          {indexer.last_checked_at && (
            <>
              {" "}
              • Last checked:{" "}
              {new Date(indexer.last_checked_at).toLocaleString()}
            </>
          )}
        </div>
        {indexer.error_message && (
          <div className="mt-1 text-[var(--color-danger-a0)] text-xs">
            {indexer.error_message}
          </div>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="small"
          onClick={handleTest}
          disabled={isTesting || isDeleting}
          title="Test connection"
        >
          {isTesting ? (
            <FaSpinner className="h-4 w-4 animate-spin" />
          ) : (
            <FaNetworkWired className="h-4 w-4" />
          )}
        </Button>
        <Button
          variant="ghost"
          size="small"
          onClick={() => onEdit(indexer)}
          title="Edit indexer"
        >
          <FaCog className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="small"
          title="Delete indexer"
          onClick={handleDelete}
          disabled={isDeleting || isTesting}
          className="text-[var(--color-danger-a0)] hover:text-[var(--color-danger-a10)]"
        >
          {isDeleting ? (
            <FaSpinner className="h-4 w-4 animate-spin" />
          ) : (
            <FaTrash className="h-4 w-4" />
          )}
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
