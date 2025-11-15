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

import { Button } from "@/components/forms/Button";
import { useModal } from "@/hooks/useModal";
import { useModalInteractions } from "@/hooks/useModalInteractions";
import { cn } from "@/libs/utils";
import type { RolePermission } from "@/services/roleService";
import { renderModalPortal } from "@/utils/modal";

export interface PermissionsModalProps {
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Callback when modal should be closed. */
  onClose: () => void;
  /** List of role permissions to display. */
  permissions: RolePermission[];
  /** Name of the role. */
  roleName: string;
}

/**
 * Permissions modal component.
 *
 * Displays all permissions for a role in a modal overlay.
 * Follows SRP by handling only permission display.
 * Follows IOC by accepting callbacks for all operations.
 * Uses DRY by leveraging useModalInteractions hook and renderModalPortal utility.
 *
 * Parameters
 * ----------
 * props : PermissionsModalProps
 *     Component props including isOpen, onClose, permissions, and roleName.
 */
export function PermissionsModal({
  isOpen,
  onClose,
  permissions,
  roleName,
}: PermissionsModalProps) {
  // Prevent body scroll when modal is open
  useModal(isOpen);

  // Use standardized modal interaction handlers (DRY, SRP)
  const { handleOverlayClick, handleModalClick, handleOverlayKeyDown } =
    useModalInteractions({ onClose });

  if (!isOpen) {
    return null;
  }

  const modalContent = (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal overlay pattern */
    <div
      className={cn("modal-overlay modal-overlay-z-1002 modal-overlay-padding")}
      onClick={handleOverlayClick}
      onKeyDown={handleOverlayKeyDown}
      role="presentation"
    >
      <div
        className={cn(
          "modal-container modal-container-shadow-large w-full max-w-2xl flex-col",
        )}
        role="dialog"
        aria-modal="true"
        aria-label={`All permissions for ${roleName}`}
        onMouseDown={handleModalClick}
      >
        <button
          type="button"
          onClick={onClose}
          className={cn(
            "modal-close-button modal-close-button-sm cursor-pointer transition-all",
            "hover:bg-[var(--color-surface-a20)] hover:text-[var(--color-text-a0)]",
          )}
          aria-label="Close"
        >
          <i className={cn("pi pi-times")} aria-hidden="true" />
        </button>

        <div className={cn("flex flex-col gap-6 p-6")}>
          <div className={cn("flex flex-col gap-2 pr-8")}>
            <h2
              className={cn(
                "m-0 font-bold text-2xl text-[var(--color-text-a0)]",
              )}
            >
              All Permissions
            </h2>
            <p
              className={cn(
                "m-0 text-[var(--color-text-a20)] text-base leading-relaxed",
              )}
            >
              Permissions for role <strong>{roleName}</strong>
            </p>
          </div>

          <div
            className={cn("flex max-h-[60vh] flex-col gap-3 overflow-y-auto")}
          >
            {permissions.length > 0 ? (
              permissions.map((rp) => (
                <div
                  key={rp.id}
                  className={cn(
                    "flex flex-col gap-2 rounded-md border border-surface-a20 bg-surface-tonal-a0 p-4",
                  )}
                >
                  <div className={cn("flex items-center gap-2")}>
                    <span
                      className={cn(
                        "inline-block rounded bg-info-a20 px-2 py-1 font-medium text-info-a0 text-xs",
                      )}
                    >
                      {rp.permission.name}
                    </span>
                    <span className={cn("text-text-a30 text-xs")}>
                      {rp.permission.resource}:{rp.permission.action}
                    </span>
                  </div>
                  {rp.permission.description && (
                    <p className={cn("m-0 text-sm text-text-a20")}>
                      {rp.permission.description}
                    </p>
                  )}
                  {rp.condition && (
                    <div className={cn("mt-1")}>
                      <span className={cn("font-medium text-text-a30 text-xs")}>
                        Condition:
                      </span>
                      <pre
                        className={cn(
                          "mt-1 rounded bg-surface-a10 p-2 text-text-a20 text-xs",
                        )}
                      >
                        {JSON.stringify(rp.condition, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className={cn("m-0 text-sm text-text-a40 italic")}>
                No permissions assigned
              </p>
            )}
          </div>

          <div className={cn("flex items-center justify-end gap-3 pt-2")}>
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
    </div>
  );

  // Render modal in a portal to avoid DOM hierarchy conflicts (DRY via utility)
  return renderModalPortal(modalContent);
}
