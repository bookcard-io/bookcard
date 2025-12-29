"use client";

import { useEffect, useState } from "react";
import { FaCheckCircle, FaExclamationCircle, FaSpinner } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { NumberInput } from "@/components/forms/NumberInput";
import { TextInput } from "@/components/forms/TextInput";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import {
  type Indexer,
  type IndexerCreate,
  IndexerProtocol,
  type IndexerTestResponse,
  IndexerType,
  type IndexerUpdate,
} from "@/types/indexer";
import { renderModalPortal } from "@/utils/modal";

interface IndexerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: IndexerCreate | IndexerUpdate) => Promise<void>;
  initialData?: Indexer;
  testConnection: (id: number) => Promise<IndexerTestResponse>;
  testNewConnection: (data: IndexerCreate) => Promise<IndexerTestResponse>;
}

export function IndexerModal({
  isOpen,
  onClose,
  onSave,
  initialData,
  testConnection,
  testNewConnection,
}: IndexerModalProps) {
  useModal(isOpen);
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  const isEditMode = !!initialData;
  const [formData, setFormData] = useState<Partial<IndexerCreate>>({
    name: "",
    indexer_type: IndexerType.TORZNAB,
    protocol: IndexerProtocol.TORRENT,
    base_url: "",
    api_key: "",
    priority: 0,
    timeout_seconds: 30,
    retry_count: 3,
    enabled: true,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isTesting, setIsTesting] = useState(false);
  const [testResult, setTestResult] = useState<IndexerTestResponse | null>(
    null,
  );

  useEffect(() => {
    if (initialData) {
      setFormData({
        name: initialData.name,
        indexer_type: initialData.indexer_type,
        protocol: initialData.protocol,
        base_url: initialData.base_url,
        api_key: initialData.api_key || "",
        priority: initialData.priority,
        timeout_seconds: initialData.timeout_seconds,
        retry_count: initialData.retry_count,
        enabled: initialData.enabled,
      });
    }
  }, [initialData]);

  const handleChange = (field: keyof IndexerCreate, value: unknown) => {
    setFormData((prev) => {
      const newData = { ...prev, [field]: value };

      // Auto-select protocol based on indexer type
      if (field === "indexer_type") {
        const type = value as IndexerType;
        if (type === IndexerType.NEWZNAB || type === IndexerType.USENET_RSS) {
          newData.protocol = IndexerProtocol.USENET;
        } else if (
          type === IndexerType.TORZNAB ||
          type === IndexerType.TORRENT_RSS
        ) {
          newData.protocol = IndexerProtocol.TORRENT;
        }
      }

      return newData;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const payload = { ...formData };

      // When editing, if the API key field is empty, it likely means it wasn't
      // returned by the server (security) and hasn't been modified by the user.
      // We remove it from the payload to avoid overwriting the existing key with an empty string.
      if (isEditMode && !payload.api_key) {
        delete payload.api_key;
      }

      await onSave(payload as IndexerCreate);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleTest = async () => {
    setIsTesting(true);
    setTestResult(null);
    try {
      let result: IndexerTestResponse;
      if (initialData) {
        result = await testConnection(initialData.id);
      } else {
        result = await testNewConnection(formData as IndexerCreate);
      }
      setTestResult(result);
    } catch (_e) {
      setTestResult({
        success: false,
        message: "Connection failed",
      });
    } finally {
      setIsTesting(false);
    }
  };

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
          "modal-container modal-container-shadow-default w-full max-w-2xl flex-col",
          "max-h-[90vh] overflow-hidden",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit Indexer" : "Add Indexer"}
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
            {isEditMode ? "Edit Indexer" : "Add Indexer"}
          </h2>
        </div>

        <form
          onSubmit={handleSubmit}
          className={cn("flex min-h-0 flex-1 flex-col overflow-hidden")}
        >
          <div
            className={cn(
              "flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6",
            )}
          >
            <TextInput
              id="name"
              label="Name"
              value={formData.name || ""}
              onChange={(e) => handleChange("name", e.target.value)}
              required
              autoFocus
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-1">
                <label
                  htmlFor="indexer_type"
                  className="font-medium text-sm text-text-a20"
                >
                  Type
                </label>
                <select
                  id="indexer_type"
                  value={formData.indexer_type}
                  onChange={(e) =>
                    handleChange("indexer_type", e.target.value as IndexerType)
                  }
                  disabled={isEditMode}
                  className={cn(
                    "rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] px-3 py-2 text-text-a0 focus:border-[var(--color-primary-a0)] focus:outline-none",
                    isEditMode && "cursor-not-allowed opacity-50",
                  )}
                >
                  {Object.values(IndexerType).map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex flex-col gap-1">
                <label
                  htmlFor="protocol"
                  className="font-medium text-sm text-text-a20"
                >
                  Protocol
                </label>
                <select
                  id="protocol"
                  value={formData.protocol}
                  onChange={(e) =>
                    handleChange("protocol", e.target.value as IndexerProtocol)
                  }
                  disabled={isEditMode}
                  className={cn(
                    "rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-tonal-a0)] px-3 py-2 text-text-a0 focus:border-[var(--color-primary-a0)] focus:outline-none",
                    isEditMode && "cursor-not-allowed opacity-50",
                  )}
                >
                  {Object.values(IndexerProtocol).map((protocol) => (
                    <option key={protocol} value={protocol}>
                      {protocol}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <TextInput
              id="base_url"
              label="URL"
              value={formData.base_url || ""}
              onChange={(e) => handleChange("base_url", e.target.value)}
              required
              placeholder="https://indexer.example.com/api"
            />

            <TextInput
              id="api_key"
              label="API Key"
              value={formData.api_key || ""}
              onChange={(e) => handleChange("api_key", e.target.value)}
              type="password"
              placeholder={
                isEditMode ? "Leave blank to keep unchanged" : undefined
              }
            />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <NumberInput
                id="priority"
                label="Priority"
                value={formData.priority || 0}
                onChange={(e) =>
                  handleChange(
                    "priority",
                    Number.parseInt(e.target.value, 10) || 0,
                  )
                }
              />
              <NumberInput
                id="timeout"
                label="Timeout (s)"
                value={formData.timeout_seconds || 30}
                onChange={(e) =>
                  handleChange(
                    "timeout_seconds",
                    Number.parseInt(e.target.value, 10) || 30,
                  )
                }
              />
              <NumberInput
                id="retries"
                label="Retries"
                value={formData.retry_count || 3}
                onChange={(e) =>
                  handleChange(
                    "retry_count",
                    Number.parseInt(e.target.value, 10) || 0,
                  )
                }
              />
            </div>

            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="enabled"
                checked={formData.enabled}
                onChange={(e) => handleChange("enabled", e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-[var(--color-primary-a0)] focus:ring-[var(--color-primary-a0)]"
              />
              <label htmlFor="enabled" className="text-sm text-text-a0">
                Enabled
              </label>
            </div>
          </div>

          <div className="modal-footer-between flex-shrink-0">
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="secondary"
                size="medium"
                onClick={handleTest}
                disabled={isTesting || isSubmitting}
              >
                {isTesting ? <FaSpinner className="mr-2 animate-spin" /> : null}
                Test
              </Button>
              {testResult && (
                <div
                  className={cn(
                    "flex items-center gap-2 text-sm",
                    testResult.success
                      ? "text-[var(--color-success-a0)]"
                      : "text-[var(--color-danger-a0)]",
                  )}
                >
                  {testResult.success ? (
                    <FaCheckCircle className="h-4 w-4" />
                  ) : (
                    <FaExclamationCircle className="h-4 w-4" />
                  )}
                  {testResult.message}
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting}
              >
                Save
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );

  return renderModalPortal(modalContent);
}
