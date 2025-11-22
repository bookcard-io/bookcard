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

import { useMemo, useState } from "react";
import { Button } from "@/components/forms/Button";
import { useAuthorEditForm } from "@/hooks/useAuthorEditForm";
import type { AuthorWithMetadata } from "@/types/author";
import {
  createDefaultTabRegistry,
  type TabKey,
} from "./components/TabRegistry";

export interface AuthorEditModalProps {
  /** Author ID to edit. */
  authorId: string | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when author is saved (for updating display). */
  onAuthorSaved?: (author: AuthorWithMetadata) => void;
}

/**
 * Modal component for editing author information.
 *
 * Follows SOLID principles:
 * - SRP: Orchestrates components and hooks, delegates responsibilities
 * - OCP: Extensible via tab registry
 * - LSP: Uses interface-based dependencies
 * - ISP: Small, focused interfaces
 * - DIP: Depends on abstractions (tab registry)
 *
 * Follows IOC by accepting dependencies as props.
 * Follows SOC by separating concerns into hooks and components.
 */
export function AuthorEditModal({
  authorId,
  onClose,
  onAuthorSaved,
}: AuthorEditModalProps) {
  const [tab, setTab] = useState<TabKey>("general");

  // Dependency injection (IOC)
  const tabRegistry = useMemo(() => createDefaultTabRegistry(), []);

  const {
    author,
    isLoading,
    error,
    formData,
    hasChanges,
    isUpdating,
    handleFieldChange,
    handleSubmit,
    handleClose,
  } = useAuthorEditForm({
    authorId,
    onClose,
    onAuthorSaved,
  });

  const handleSaveClick = async (e: React.FormEvent) => {
    e.preventDefault();
    await handleSubmit(e);
    // Note: handleSubmit will handle closing if auto-dismiss is enabled
  };

  if (!authorId) {
    return null;
  }

  if (isLoading) {
    return (
      <div
        className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
        role="dialog"
        aria-modal
      >
        <div className="modal-container modal-container-shadow-default flex h-[550px] w-full max-w-3xl flex-col overflow-hidden">
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            Loading author data...
          </div>
        </div>
      </div>
    );
  }

  if (error || !author) {
    return (
      <div
        className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
        role="dialog"
        aria-modal
      >
        <div className="modal-container modal-container-shadow-default flex h-[550px] w-full max-w-3xl flex-col overflow-hidden">
          <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-8 text-base text-text-a30">
            {error || "Author not found"}
            <button
              type="button"
              className="rounded-md bg-surface-a30 px-4 py-2 font-semibold text-text-a0 transition-colors hover:bg-surface-a40"
              onClick={handleClose}
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  const tabs = tabRegistry.getAll();
  const currentTab = tabRegistry.get(tab);

  return (
    <div
      className="fixed inset-0 z-[1000] flex items-center justify-center bg-black/70"
      role="dialog"
      aria-modal
    >
      <div className="modal-container modal-container-shadow-default relative flex h-[550px] w-full max-w-3xl flex-col overflow-hidden">
        <button
          type="button"
          onClick={handleClose}
          className="modal-close-button modal-close-button-sm focus:outline"
          aria-label="Close"
        >
          <i className="pi pi-times" aria-hidden="true" />
        </button>
        <div className="modal-header flex-shrink-0">
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <h2 className="m-0 hidden truncate font-bold text-2xl text-text-a0 leading-[1.4] md:block">
              Editing {author.name}
            </h2>
            <p className="m-0 hidden text-sm text-text-a30 leading-6 md:block">
              Edit author metadata and information.
            </p>
          </div>
        </div>
        <div className="flex min-h-0 flex-1">
          <nav className="w-[160px] flex-shrink-0 border-surface-a20 border-r bg-surface-a0 p-4 px-3">
            {tabs.map((tabConfig) => {
              const iconMap: Record<TabKey, string> = {
                general: "pi-align-justify",
                tags: "pi-tags",
                photo: "pi-user",
                advanced: "pi-cog",
              };
              const isActive = tab === tabConfig.key;
              return (
                <button
                  key={tabConfig.key}
                  type="button"
                  className={`w-full rounded-md border-none p-3 px-[10px] text-left text-sm transition-colors ${
                    isActive
                      ? "bg-surface-a20 font-medium text-primary-a0"
                      : "bg-transparent text-text-a0 hover:bg-surface-a20"
                  } flex items-center gap-2`}
                  onClick={() => setTab(tabConfig.key)}
                >
                  <i
                    className={`pi ${iconMap[tabConfig.key]} text-base`}
                    aria-hidden="true"
                  />
                  {tabConfig.label}
                </button>
              );
            })}
          </nav>
          <div className="min-h-0 min-w-0 flex-1 overflow-y-auto p-[15px_20px]">
            {currentTab?.render({
              author,
              form: formData,
              onFieldChange: handleFieldChange,
            })}
          </div>
        </div>
        <div className="modal-footer-between flex-shrink-0">
          <div className="flex w-full flex-1 flex-col gap-2" />
          <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
            <Button
              type="button"
              variant="ghost"
              size="xsmall"
              className="sm:px-6 sm:py-3 sm:text-base"
              onClick={handleClose}
              disabled={isUpdating}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="primary"
              size="xsmall"
              className="sm:px-6 sm:py-3 sm:text-base"
              onClick={handleSaveClick}
              loading={isUpdating}
              disabled={!hasChanges}
            >
              Save Changes
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
