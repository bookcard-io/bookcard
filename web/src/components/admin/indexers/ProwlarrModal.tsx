"use client";

import { useEffect, useState } from "react";
import { FaSync } from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import { MultiTextInput } from "@/components/forms/MultiTextInput";
import { NumberInput } from "@/components/forms/NumberInput";
import { TextInput } from "@/components/forms/TextInput";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { useProwlarr } from "@/hooks/useProwlarr";
import { cn } from "@/libs/utils";
import type { ProwlarrConfigUpdate } from "@/types/prowlarr";
import { renderModalPortal } from "@/utils/modal";

interface ProwlarrModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
}

export function ProwlarrModal({
  isOpen,
  onClose,
  onSuccess,
}: ProwlarrModalProps) {
  useModal(isOpen);
  const { showSuccess, showDanger } = useGlobalMessages();
  const { config, isLoading, isSyncing, updateConfig, syncIndexers } =
    useProwlarr();
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  const [formData, setFormData] = useState<ProwlarrConfigUpdate>({
    url: "http://localhost:9696",
    api_key: "",
    enabled: false,
    sync_interval_minutes: 60,
    sync_categories: ["Audio", "Books"],
    sync_app_profiles: [],
  });

  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (config) {
      setFormData({
        url: config.url,
        api_key: config.api_key || "",
        enabled: config.enabled,
        sync_interval_minutes: config.sync_interval_minutes,
        sync_categories:
          config.sync_categories && config.sync_categories.length > 0
            ? config.sync_categories
            : ["Audio", "Books"],
        sync_app_profiles: config.sync_app_profiles || [],
      });
    }
  }, [config]);

  const handleChange = (field: keyof ProwlarrConfigUpdate, value: unknown) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await updateConfig(formData);
      showSuccess("Prowlarr configuration saved.");
      onSuccess();
      onClose();
    } catch (error) {
      showDanger(
        `Failed to save Prowlarr configuration: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSync = async () => {
    try {
      // Save config first if enabled
      if (formData.enabled) {
        await updateConfig(formData);
      }

      const result = await syncIndexers();
      showSuccess(
        `Sync completed: ${result.added} added, ${result.updated} updated, ${result.removed} removed.`,
      );
      onSuccess();
    } catch (error) {
      showDanger(
        `Sync failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      );
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
        aria-label="Prowlarr Integration"
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
          <h2 className="m-0 flex items-center gap-2 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
            <span style={{ color: "#e66000" }}>Prowlarr</span> Integration
          </h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-center text-text-a30">
            Loading configuration...
          </div>
        ) : (
          <form
            onSubmit={handleSave}
            className={cn("flex min-h-0 flex-1 flex-col overflow-hidden")}
          >
            <div
              className={cn(
                "flex min-h-0 flex-1 flex-col gap-6 overflow-y-auto p-6",
              )}
            >
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="enabled"
                  checked={formData.enabled}
                  onChange={(e) => handleChange("enabled", e.target.checked)}
                  className="h-4 w-4 rounded border-gray-300 text-[var(--color-primary-a0)] focus:ring-[var(--color-primary-a0)]"
                />
                <label
                  htmlFor="enabled"
                  className="font-medium text-sm text-text-a0"
                >
                  Enable Prowlarr Integration
                </label>
              </div>

              <TextInput
                id="url"
                label="Server URL"
                value={formData.url}
                onChange={(e) => handleChange("url", e.target.value)}
                required
                placeholder="http://localhost:9696"
                disabled={!formData.enabled}
              />

              <TextInput
                id="api_key"
                label="API Key"
                value={formData.api_key || ""}
                onChange={(e) => handleChange("api_key", e.target.value)}
                type="password"
                required={formData.enabled}
                disabled={!formData.enabled}
              />

              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                <NumberInput
                  id="sync_interval"
                  label="Sync Interval (Minutes)"
                  value={formData.sync_interval_minutes}
                  onChange={(e) =>
                    handleChange(
                      "sync_interval_minutes",
                      Number.parseInt(e.target.value, 10) || 60,
                    )
                  }
                  min={10}
                  disabled={!formData.enabled}
                />
              </div>

              <MultiTextInput
                id="sync_categories"
                label="Sync Categories"
                values={formData.sync_categories || []}
                onChange={(values) => handleChange("sync_categories", values)}
                placeholder="Add category names (e.g., Audio, Books)"
                helperText="Enter category names to filter which indexers to sync. Leave empty to sync all categories."
                disabled={!formData.enabled}
              />

              {/* Note: sync_app_profiles could be added here as MultiSelect in the future */}
            </div>

            <div className="modal-footer-between flex-shrink-0">
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="secondary"
                  size="medium"
                  onClick={handleSync}
                  disabled={!formData.enabled || isSubmitting || isSyncing}
                >
                  <FaSync
                    className={cn("mr-2 h-4 w-4", isSyncing && "animate-spin")}
                  />
                  {isSyncing ? "Syncing..." : "Sync now"}
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="ghost"
                  size="medium"
                  onClick={onClose}
                  disabled={isSubmitting || isSyncing}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="medium"
                  loading={isSubmitting}
                  disabled={isSyncing}
                >
                  Save
                </Button>
              </div>
            </div>
          </form>
        )}
      </div>
    </div>
  );

  return renderModalPortal(modalContent);
}
