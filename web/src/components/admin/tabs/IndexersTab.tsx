"use client";

import { useCallback, useState } from "react";
import { FaPlus, FaSync } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useIndexers } from "@/hooks/useIndexers";
import type { Indexer, IndexerCreate, IndexerUpdate } from "@/types/indexer";
import { IndexerList } from "../indexers/IndexerList";
import { IndexerModal } from "../indexers/IndexerModal";
import { ProwlarrModal } from "../indexers/ProwlarrModal";

export function IndexersTab() {
  const { showSuccess, showDanger } = useGlobalMessages();
  const {
    indexers,
    isLoading,
    createIndexer,
    updateIndexer,
    deleteIndexer,
    testConnection,
    testNewConnection,
    refresh,
  } = useIndexers();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isProwlarrModalOpen, setIsProwlarrModalOpen] = useState(false);
  const [editingIndexer, setEditingIndexer] = useState<Indexer | undefined>(
    undefined,
  );

  const handleCreate = useCallback(() => {
    setEditingIndexer(undefined);
    setIsModalOpen(true);
  }, []);

  const handleEdit = useCallback((indexer: Indexer) => {
    setEditingIndexer(indexer);
    setIsModalOpen(true);
  }, []);

  const handleDelete = useCallback(
    async (indexer: Indexer) => {
      if (
        !confirm(`Are you sure you want to delete indexer "${indexer.name}"?`)
      ) {
        return;
      }
      try {
        await deleteIndexer(indexer.id);
        showSuccess(`Indexer "${indexer.name}" deleted successfully.`);
      } catch (error) {
        showDanger(
          `Failed to delete indexer: ${error instanceof Error ? error.message : "Unknown error"}`,
        );
      }
    },
    [deleteIndexer, showSuccess, showDanger],
  );

  const handleSave = useCallback(
    async (data: IndexerCreate | IndexerUpdate) => {
      try {
        if (editingIndexer) {
          await updateIndexer(editingIndexer.id, data as IndexerUpdate);
          showSuccess(`Indexer "${data.name}" updated successfully.`);
        } else {
          await createIndexer(data as IndexerCreate);
          showSuccess(`Indexer "${data.name}" created successfully.`);
        }
        setIsModalOpen(false);
      } catch (error) {
        showDanger(
          `Failed to save indexer: ${error instanceof Error ? error.message : "Unknown error"}`,
        );
      }
    },
    [editingIndexer, updateIndexer, createIndexer, showSuccess, showDanger],
  );

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg text-text-a0">Indexers</h2>
        <div className="flex items-center gap-2">
          <Button
            onClick={() => setIsProwlarrModalOpen(true)}
            variant="secondary"
            size="small"
            style={{
              borderColor: "#e66000",
              color: "#e66000",
            }}
          >
            <FaSync className="mr-2" />
            Prowlarr sync
          </Button>
          <Button onClick={handleCreate} size="small">
            <FaPlus className="mr-2" />
            Add indexer
          </Button>
        </div>
      </div>

      <div className="rounded-md border border-[var(--color-primary-a20)] bg-[var(--color-surface-tonal-a0)] p-4">
        <p className="text-sm text-text-a0">
          Bookcard supports generic Torznab (Torrent) and Newznab (Usenet)
          indexers directly. For indexers with custom APIs (like MyAnonamouse or
          AvistaZ), please use <strong>Prowlarr</strong> to manage them and sync
          them here.
        </p>
      </div>

      <IndexerList
        indexers={indexers}
        isLoading={isLoading}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      {isModalOpen && (
        <IndexerModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSave={handleSave}
          initialData={editingIndexer}
          testConnection={testConnection}
          testNewConnection={testNewConnection}
        />
      )}

      {isProwlarrModalOpen && (
        <ProwlarrModal
          isOpen={isProwlarrModalOpen}
          onClose={() => setIsProwlarrModalOpen(false)}
          onSuccess={() => {
            // Refresh indexers list after Prowlarr changes
            refresh();
          }}
        />
      )}
    </div>
  );
}
