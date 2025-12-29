"use client";

import { useCallback, useEffect, useState } from "react";
import { FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import type {
  DownloadClient,
  DownloadItemResponse,
} from "@/types/downloadClient";
import { renderModalPortal } from "@/utils/modal";

interface DownloadClientItemsModalProps {
  isOpen: boolean;
  onClose: () => void;
  client: DownloadClient;
  getItems: (
    id: number,
  ) => Promise<{ items: DownloadItemResponse[]; total: number }>;
}

export function DownloadClientItemsModal({
  isOpen,
  onClose,
  client,
  getItems,
}: DownloadClientItemsModalProps) {
  useModal(isOpen);
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  const [items, setItems] = useState<DownloadItemResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getItems(client.id);
      setItems(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load items");
    } finally {
      setIsLoading(false);
    }
  }, [client.id, getItems]);

  useEffect(() => {
    if (isOpen) {
      fetchItems();
    }
  }, [isOpen, fetchItems]);

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-1002 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-default w-full max-w-3xl flex-col",
          "max-h-[80vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={`Active Downloads - ${client.name}`}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>

        <div className="flex items-start justify-between gap-4 border-surface-a20 border-b pt-6 pr-16 pb-4 pl-6">
          <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
            Active Downloads - {client.name}
          </h2>
          <Button
            variant="secondary"
            size="small"
            onClick={fetchItems}
            disabled={isLoading}
          >
            Refresh
          </Button>
        </div>

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-8 text-text-a30">
              <FaSpinner className="mr-2 animate-spin" />
              Loading downloads...
            </div>
          ) : error ? (
            <div className="rounded bg-[var(--color-danger-a10)] p-4 text-[var(--color-danger-a0)]">
              {error}
            </div>
          ) : items.length === 0 ? (
            <div className="text-center text-text-a30 italic">
              No active downloads found.
            </div>
          ) : (
            <div className="flex flex-col gap-2 overflow-y-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-surface-a20 border-b text-text-a30">
                    <th className="px-2 py-2 font-medium">Title</th>
                    <th className="px-2 py-2 font-medium">Status</th>
                    <th className="px-2 py-2 font-medium">Progress</th>
                    <th className="px-2 py-2 font-medium">ETA</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr
                      key={item.client_item_id}
                      className="border-surface-a10 border-b last:border-0 hover:bg-surface-a10"
                    >
                      <td
                        className="max-w-[300px] truncate px-2 py-3 text-text-a0"
                        title={item.title}
                      >
                        {item.title}
                      </td>
                      <td className="px-2 py-3 text-text-a20 capitalize">
                        {item.status}
                      </td>
                      <td className="px-2 py-3 text-text-a20">
                        {(item.progress * 100).toFixed(1)}%
                      </td>
                      <td className="px-2 py-3 text-text-a20">
                        {item.eta_seconds
                          ? formatDuration(item.eta_seconds)
                          : "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="modal-footer flex-shrink-0">
          <Button
            type="button"
            variant="secondary"
            size="medium"
            onClick={onClose}
          >
            Close
          </Button>
        </div>
      </div>
    </div>
  );

  return renderModalPortal(modalContent);
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`;
}
