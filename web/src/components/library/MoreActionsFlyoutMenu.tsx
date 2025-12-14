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

import { useCallback, useEffect, useMemo, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useUser } from "@/contexts/UserContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { useTaskTerminalPolling } from "@/hooks/useTaskTerminalPolling";
import { cn } from "@/libs/utils";
import { stripBookDrm } from "@/services/bookService";
import type { Book } from "@/types/book";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";
import { buildBookPermissionContext } from "@/utils/permissions";

export interface MoreActionsFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Book to perform actions on. */
  book: Book;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback on successful action (to close parent menu). */
  onSuccess?: () => void;
  /** Callback to close parent menu (for Esc key handling). */
  onCloseParent?: () => void;
}

/**
 * Flyout menu for additional book actions ("More...").
 *
 * Currently contains a single action: strip DRM (if present), executed as a
 * fire-and-forget background task with terminal polling and global messaging.
 */
export function MoreActionsFlyoutMenu({
  isOpen,
  parentItemRef,
  book,
  onClose,
  onMouseEnter,
  onSuccess,
  onCloseParent,
}: MoreActionsFlyoutMenuProps) {
  const [mounted, setMounted] = useState(false);
  const { canPerformAction } = useUser();
  const { showDanger, showInfo, showSuccess, showWarning } =
    useGlobalMessages();
  const taskTerminalPolling = useTaskTerminalPolling();

  const canWrite = useMemo(
    () => canPerformAction("books", "write", buildBookPermissionContext(book)),
    [book, canPerformAction],
  );

  const { position, direction, menuRef } = useFlyoutPosition({
    isOpen,
    parentItemRef,
    mounted,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  // Keep flyout open while pointer is within padded union of parent + flyout.
  useFlyoutIntent({
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding: 10,
    minMovementPx: 2,
    idleTimeMs: 20,
  });

  /**
   * Handle mouse entering the flyout menu.
   */
  const handleFlyoutMouseEnter = useCallback(() => {
    onMouseEnter?.();
  }, [onMouseEnter]);

  const handleStripDrm = useCallback(() => {
    if (!canWrite) {
      return;
    }

    stripBookDrm(book.id)
      .then(({ task_id, message }) => {
        if (task_id <= 0) {
          showSuccess(message || "No DRM stripping needed");
          return;
        }

        showInfo(message || "DRM stripping queued");

        void taskTerminalPolling.pollToTerminal(task_id).then((task) => {
          if (!task) {
            showDanger(
              "DRM stripping is taking longer than expected. Check the tasks panel for updates.",
            );
            return;
          }

          if (task.status === "completed") {
            const didStrip =
              task.metadata &&
              typeof task.metadata.did_strip === "boolean" &&
              task.metadata.did_strip;
            const outputFormat =
              task.metadata && typeof task.metadata.output_format === "string"
                ? task.metadata.output_format
                : null;

            if (didStrip) {
              showSuccess(
                outputFormat
                  ? `DRM stripped and added as ${outputFormat}`
                  : "DRM stripped successfully",
              );
            } else {
              showSuccess("No DRM detected; nothing to do");
            }
            return;
          }

          if (task.status === "cancelled") {
            showWarning("DRM stripping cancelled");
            return;
          }

          // failed
          showDanger(task.error_message || "DRM stripping failed");
        });
      })
      .catch((error) => {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to strip DRM";
        showDanger(errorMessage);
      });

    // Close UI immediately (fire-and-forget)
    onClose();
    onSuccess?.();
  }, [
    book.id,
    canWrite,
    onClose,
    onSuccess,
    showDanger,
    showInfo,
    showSuccess,
    showWarning,
    taskTerminalPolling,
  ]);

  // Handle Esc key to close menus
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
        onCloseParent?.();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, onClose, onCloseParent]);

  if (!isOpen || !mounted) {
    return null;
  }

  const menuContent = (
    <div
      ref={menuRef}
      className={cn(
        "fixed z-[10000] rounded-md",
        "border border-surface-tonal-a20 bg-surface-tonal-a10",
        "shadow-black/50 shadow-lg",
        "overflow-hidden",
        "min-w-[220px]",
      )}
      style={getFlyoutPositionStyle(position, direction)}
      role="menu"
      aria-label="More actions"
      onMouseDown={(e) => e.stopPropagation()}
      onMouseEnter={handleFlyoutMouseEnter}
      data-keep-selection
    >
      <div className="py-1">
        <DropdownMenuItem
          label="Strip DRM if present"
          onClick={canWrite ? handleStripDrm : undefined}
          disabled={!canWrite}
        />
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
