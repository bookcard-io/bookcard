"use client";

import { useCallback, useState } from "react";
import { FaPlus } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useDownloadClients } from "@/hooks/useDownloadClients";
import type {
  DownloadClient,
  DownloadClientCreate,
  DownloadClientUpdate,
} from "@/types/downloadClient";
import { DownloadClientItemsModal } from "../download-clients/DownloadClientItemsModal";
import { DownloadClientList } from "../download-clients/DownloadClientList";
import { DownloadClientModal } from "../download-clients/DownloadClientModal";

export function DownloadClientsTab() {
  const { showSuccess, showDanger } = useGlobalMessages();
  const {
    downloadClients,
    isLoading,
    createDownloadClient,
    updateDownloadClient,
    deleteDownloadClient,
    testConnection,
    testNewConnection,
    getClientItems,
  } = useDownloadClients();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<
    DownloadClient | undefined
  >(undefined);
  const [viewingItemsClient, setViewingItemsClient] = useState<
    DownloadClient | undefined
  >(undefined);

  const handleCreate = useCallback(() => {
    setEditingClient(undefined);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((client: DownloadClient) => {
    setEditingClient(client);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(
    async (client: DownloadClient) => {
      if (
        !confirm(
          `Are you sure you want to delete download client "${client.name}"?`,
        )
      ) {
        return;
      }
      try {
        await deleteDownloadClient(client.id);
        showSuccess(`Download client "${client.name}" deleted successfully.`);
      } catch (error) {
        showDanger(
          `Failed to delete download client: ${
            error instanceof Error ? error.message : "Unknown error"
          }`,
        );
      }
    },
    [deleteDownloadClient, showSuccess, showDanger],
  );

  const handleSave = useCallback(
    async (data: DownloadClientCreate | DownloadClientUpdate) => {
      try {
        if (editingClient) {
          await updateDownloadClient(
            editingClient.id,
            data as DownloadClientUpdate,
          );
          showSuccess(`Download client "${data.name}" updated successfully.`);
        } else {
          await createDownloadClient(data as DownloadClientCreate);
          showSuccess(`Download client "${data.name}" created successfully.`);
        }
        setIsModalOpen(false);
      } catch (error) {
        showDanger(
          `Failed to save download client: ${
            error instanceof Error ? error.message : "Unknown error"
          }`,
        );
      }
    },
    [
      editingClient,
      updateDownloadClient,
      createDownloadClient,
      showSuccess,
      showDanger,
    ],
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg text-text-a0">Download Clients</h2>
        <div className="flex items-center gap-2">
          <Button onClick={handleCreate} size="small">
            <FaPlus className="mr-2" />
            Add client
          </Button>
        </div>
      </div>

      <div className="rounded-md border border-[var(--color-primary-a20)] bg-[var(--color-surface-tonal-a0)] p-4">
        <p className="text-sm text-text-a0">
          Bookcard supports various download clients including qBittorrent,
          Transmission, and others.
        </p>
      </div>

      <DownloadClientList
        clients={downloadClients}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onViewItems={(client) => setViewingItemsClient(client)}
      />

      {isModalOpen && (
        <DownloadClientModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleSave}
          initialData={editingClient}
          testConnection={testConnection}
          testNewConnection={testNewConnection}
        />
      )}

      {viewingItemsClient && (
        <DownloadClientItemsModal
          isOpen={!!viewingItemsClient}
          onClose={() => setViewingItemsClient(undefined)}
          client={viewingItemsClient}
          getItems={getClientItems}
        />
      )}
    </div>
  );
}
