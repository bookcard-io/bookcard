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

import { useCallback, useMemo, useState } from "react";
import { Button } from "@/components/forms/Button";
import { TextArea } from "@/components/forms/TextArea";
import { TextInput } from "@/components/forms/TextInput";
import { MagicShelfRulesEditor } from "@/components/shelves/MagicShelfRulesEditor";
import { ShelfCoverSection } from "@/components/shelves/ShelfCoverSection";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useUser } from "@/contexts/UserContext";
import { useShelfEditState } from "@/hooks/shelves/useShelfEditState";
import { useShelfImport } from "@/hooks/shelves/useShelfImport";
import { useCoverFile } from "@/hooks/useCoverFile";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { useShelfCoverOperations } from "@/hooks/useShelfCoverOperations";
import { useShelfForm } from "@/hooks/useShelfForm";
import { cn } from "@/libs/utils";
import { importReadList } from "@/services/shelfService";
import {
  type FilterGroup,
} from "@/types/magicShelf";
import type { Shelf, ShelfCreate, ShelfUpdate } from "@/types/shelf";
import {
  comicRackImportStrategy,
  type FileImportStrategy,
} from "@/utils/importStrategies";
import { buildShelfPermissionContext } from "@/utils/permissions";
import { SHELF_ACTION, SHELF_RESOURCE } from "@/utils/shelfConstants";
import { getErrorMessage, prepareShelfData } from "@/utils/shelfEditHelpers";

export interface ShelfEditModalProps {
  /** Shelf to edit (null for create mode). */
  shelf: Shelf | null;
  /** Initial name for create mode (overrides shelf name if shelf is null). */
  initialName?: string;
  /** Initial cover file for create mode (e.g., from book cover). */
  initialCoverFile?: File | null;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** Callback when shelf is saved. Returns the created/updated shelf. */
  onSave: (
    data: ShelfCreate | ShelfUpdate,
    options?: { readListFile?: File | null },
  ) => Promise<Shelf>;
  /** Callback when cover picture is uploaded. Receives updated shelf with new cover. */
  onCoverSaved?: (shelf: Shelf) => void;
  /** Callback when cover picture is deleted. Receives updated shelf without cover. */
  onCoverDeleted?: (shelf: Shelf) => void;
  /** Strategy for importing files. Defaults to ComicRack .cbl. */
  importStrategy?: FileImportStrategy;
  /** Callback to import a reading list file. */
  onImport?: (shelfId: number, file: File) => Promise<void>;
}

type TabId = "rules" | "import";

/**
 * Shelf create/edit modal component.
 *
 * Displays a form for creating or editing a shelf in a modal overlay.
 * Follows SRP by delegating concerns to specialized hooks and components.
 * Follows IOC by accepting callbacks for all operations.
 * Follows DRY by reusing hooks and components.
 */
export function ShelfEditModal({
  shelf,
  initialName,
  initialCoverFile,
  onClose,
  onSave,
  onCoverSaved,
  onCoverDeleted,
  importStrategy = comicRackImportStrategy,
  onImport,
}: ShelfEditModalProps) {
  const isEditMode = shelf !== null;
  const { canPerformAction } = useUser();
  const { showDanger } = useGlobalMessages();
  const [activeTab, setActiveTab] = useState<TabId>("rules");

  // Permission logic
  const hasPermission = useMemo(() => {
    if (isEditMode) {
      const shelfContext = buildShelfPermissionContext(shelf);
      return canPerformAction(
        SHELF_RESOURCE.SHELVES,
        SHELF_ACTION.EDIT,
        shelfContext,
      );
    }
    return canPerformAction(SHELF_RESOURCE.SHELVES, SHELF_ACTION.CREATE);
  }, [isEditMode, shelf, canPerformAction]);

  // State hooks
  const {
    coverOperationError,
    setCoverOperationError,
    isSaving,
    setIsSaving,
    reset: resetState,
  } = useShelfEditState();

  // Form hook
  const {
    name,
    description,
    isPublic,
    filterRules,
    isSubmitting,
    errors,
    setName,
    setDescription,
    setIsPublic,
    setFilterRules,
    handleSubmit: validateAndSubmit,
    reset: resetForm,
  } = useShelfForm({
    initialName: shelf?.name ?? initialName ?? "",
    initialDescription: shelf?.description ?? null,
    initialIsPublic: shelf?.is_public ?? false,
    initialFilterRules: (shelf?.filter_rules as unknown as FilterGroup) ?? null,
    onSubmit: async () => {
      // This won't be called since we handle submission manually
    },
    onError: (error) => showDanger(error),
  });

  // Cover file hook
  const {
    coverFile,
    coverPreviewUrl,
    coverError,
    isCoverDeleteStaged,
    fileInputRef,
    handleCoverFileChange,
    handleClearCoverFile,
    handleCoverDelete,
    handleCancelDelete,
    reset: resetCover,
  } = useCoverFile({
    initialCoverFile,
    isEditMode,
  });

  // Import hook
  const {
    importFile,
    handleFileChange: handleImportFileChange,
    resetImport,
  } = useShelfImport({
    strategy: importStrategy,
    enabled: !isEditMode,
    onParseSuccess: (data) => {
      if (data.name) setName(data.name);
      if (data.description) setDescription(data.description);
    },
    onError: (error) => {
      showDanger(getErrorMessage(error, "Failed to parse file"));
    },
  });

  // Cover operations hook
  const { executeCoverOperations } = useShelfCoverOperations({
    onCoverSaved,
    onCoverDeleted,
    onError: (error) => {
      setCoverOperationError(error);
      showDanger(error);
    },
  });

  // Modal hooks
  useModal(true);
  const { handleOverlayClick, handleModalClick } = useModalInteractions({
    onClose,
  });

  const handleOverlayKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      if (e.key === "Escape") {
        onClose();
      }
    },
    [onClose],
  );

  const handleCoverFileChangeWithErrorClear = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setCoverOperationError(null);
      handleCoverFileChange(e);
    },
    [handleCoverFileChange, setCoverOperationError],
  );

  const handleCancel = useCallback(() => {
    resetForm();
    resetCover();
    resetState();
    resetImport();
    onClose();
  }, [resetForm, resetCover, resetState, resetImport, onClose]);

  const performImport = async (shelfId: number, file: File) => {
    if (onImport) {
      await onImport(shelfId, file);
    } else {
      // Default fallback if not injected
      await importReadList(
        shelfId,
        { importer: importStrategy.importerType, auto_add_matched: true },
        file,
      );
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate form first
    const isValid = await validateAndSubmit();
    if (!isValid) {
      return;
    }

    setIsSaving(true);
    setCoverOperationError(null);

    try {
      // Prepare shelf data
      const data = prepareShelfData(name, description, isPublic);

      // Determine shelf type and attach rules
      if (filterRules && filterRules.rules.length > 0) {
        data.shelf_type = "magic_shelf";
        data.filter_rules = filterRules as unknown as Record<string, unknown>;
      } else if (importFile) {
        data.shelf_type = "read_list";
        data.filter_rules = null;
      } else {
        data.shelf_type = "shelf";
        data.filter_rules = null;
      }

      // Save the shelf and get the result. For create mode, optionally
      // include the read list file so the API can import it in a single call.
      const saveOptions =
        !isEditMode && importFile ? { readListFile: importFile } : undefined;
      const savedShelf = await onSave(data, saveOptions);

      // Handle import in edit mode (after shelf is saved)
      if (isEditMode && importFile && savedShelf) {
        try {
          await performImport(savedShelf.id, importFile);
        } catch (error) {
          showDanger(getErrorMessage(error, "Failed to import reading list"));
          // Don't close modal on import error so user can retry
          return;
        }
      }

      // Handle cover operations after shelf is saved
      if (savedShelf && (coverFile || isCoverDeleteStaged)) {
        await executeCoverOperations(
          savedShelf,
          coverFile,
          isCoverDeleteStaged,
        );
      }

      onClose();
    } catch (error) {
      showDanger(getErrorMessage(error, "Failed to save shelf"));
      // Error handling is done by useShelfForm and useShelfCoverOperations
    } finally {
      setIsSaving(false);
    }
  };

  const isFormDisabled = !hasPermission;
  const isActionDisabled = !hasPermission || isSubmitting || isSaving;

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
  };

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className="modal-overlay modal-overlay-z-50 modal-overlay-padding"
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
      data-keep-selection
    >
      <div
        className="modal-container modal-container-shadow-default max-h-[calc(100dvh-2rem)] w-full max-w-4xl flex-col overflow-hidden"
        role="dialog"
        aria-modal="true"
        aria-label={isEditMode ? "Edit shelf" : "Create shelf"}
        onMouseDown={handleModalClick}
        data-keep-selection
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
          <div className="flex min-w-0 flex-1 flex-col gap-1">
            <h2 className="m-0 truncate font-bold text-2xl text-text-a0 leading-[1.4]">
              {isEditMode ? "Edit shelf" : "Create shelf"}
            </h2>
          </div>
        </div>

        <form
          onSubmit={handleFormSubmit}
          className="flex min-h-0 flex-1 flex-col"
        >
          <div className="grid min-h-0 flex-1 grid-cols-1 gap-6 overflow-y-auto p-6">
            {!hasPermission && (
              <div
                className="rounded-md bg-warning-a20 px-4 py-3 text-sm text-warning-a0"
                role="alert"
              >
                {isEditMode
                  ? "You don't have permission to edit this shelf."
                  : "You don't have permission to create shelves."}
              </div>
            )}

            {/* Top Section: Cover and Basic Info */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-[200px_1fr]">
              {/* Left Column: Cover */}
              <div className="flex flex-col gap-4">
                <ShelfCoverSection
                  shelf={shelf}
                  isEditMode={isEditMode}
                  isCoverDeleteStaged={isCoverDeleteStaged}
                  coverPreviewUrl={coverPreviewUrl}
                  coverError={coverError || coverOperationError}
                  fileInputRef={fileInputRef}
                  isSaving={isSaving || isFormDisabled}
                  onCoverFileChange={handleCoverFileChangeWithErrorClear}
                  onClearCoverFile={handleClearCoverFile}
                  onCoverDelete={handleCoverDelete}
                  onCancelDelete={handleCancelDelete}
                />
              </div>

              {/* Right Column: Name and Description */}
              <div className="flex flex-col gap-4">
                <TextInput
                  label="Shelf name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  error={errors.name}
                  required
                  autoFocus
                  disabled={isFormDisabled}
                />

                <TextArea
                  label="Description"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  error={errors.description}
                  rows={2}
                  placeholder="Optional description of the shelf"
                  disabled={isFormDisabled}
                />

                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="isPublic"
                    checked={isPublic}
                    onChange={(e) => setIsPublic(e.target.checked)}
                    disabled={isFormDisabled}
                    className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                  <label
                    htmlFor="isPublic"
                    className="cursor-pointer text-base text-text-a0 disabled:cursor-not-allowed"
                  >
                    Share with everyone
                  </label>
                </div>
              </div>
            </div>

            {/* Tabs Section */}
            <div className="flex flex-col gap-4">
              <div className="flex gap-2 border-[var(--color-surface-a20)] border-b">
                <button
                  type="button"
                  className={cn(
                    "-mb-px relative cursor-pointer border-0 border-transparent border-b-2 bg-transparent px-6 py-3 font-medium text-sm text-text-a30 transition-[color,border-color] duration-200",
                    "hover:text-text-a10",
                    activeTab === "rules" &&
                      "border-b-[var(--color-primary-a0)] text-text-a0",
                  )}
                  onClick={() => handleTabChange("rules")}
                >
                  Magic shelf
                </button>
                <button
                  type="button"
                  className={cn(
                    "-mb-px relative cursor-pointer border-0 border-transparent border-b-2 bg-transparent px-6 py-3 font-medium text-sm text-text-a30 transition-[color,border-color] duration-200",
                    "hover:text-text-a10",
                    activeTab === "import" &&
                      "border-b-[var(--color-primary-a0)] text-text-a0",
                  )}
                  onClick={() => handleTabChange("import")}
                >
                  ComicRack (.cbl)
                </button>
              </div>

              <div className="px-0 py-3.5">
                {activeTab === "rules" && (
                  <div className="flex flex-col gap-4">
                    <p className="text-sm text-text-a30">
                      Create dynamic rules to automatically populate this shelf.
                    </p>
                    <div className="[&_button]:!h-9 [&_input]:!h-9 [&_select]:!h-9">
                      <MagicShelfRulesEditor
                        rootGroup={filterRules}
                        onChange={setFilterRules}
                        disabled={isFormDisabled}
                      />
                    </div>
                  </div>
                )}

                {activeTab === "import" && (
                  <div className="space-y-4">
                    <div className="font-medium text-sm text-text-a10">
                      {isEditMode
                        ? `Import ${importStrategy.label}`
                        : `Create from ${importStrategy.label}`}
                    </div>
                    <input
                      id="readlist-import-input"
                      type="file"
                      accept={importStrategy.accept}
                      onChange={handleImportFileChange}
                      disabled={isFormDisabled}
                      className="block w-full rounded-md border border-surface-a20 bg-surface-a0 px-4 py-3 font-inherit text-base text-text-a0 leading-normal transition-[border-color_0.2s,box-shadow_0.2s,background-color_0.2s] file:mr-4 file:cursor-pointer file:rounded file:border-0 file:bg-surface-a20 file:px-4 file:py-2 file:font-semibold file:text-sm file:text-text-a0 hover:file:bg-surface-a30 focus:border-primary-a0 focus:bg-surface-a10 focus:shadow-[var(--shadow-focus-ring)] focus:outline-none hover:not(:focus):border-surface-a30 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                    <p className="text-sm text-text-a30">
                      Importing a reading list will create a static shelf with
                      the books from the file.
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="modal-footer-between">
            <div className="flex w-full flex-1 flex-col gap-2">
              {/* Error messages can go here if needed */}
            </div>
            <div className="flex w-full flex-shrink-0 flex-col-reverse justify-end gap-3 md:w-auto md:flex-row">
              <Button
                type="button"
                variant="ghost"
                size="medium"
                onClick={handleCancel}
                disabled={isActionDisabled}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="medium"
                loading={isSubmitting || isSaving}
                disabled={isActionDisabled}
              >
                {isEditMode ? "Save" : "Create"}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
