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

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import { useGlobalMessages } from "@/contexts/GlobalMessageContext";
import { useSelectedBooks } from "@/contexts/SelectedBooksContext";
import type { EReaderDevice } from "@/contexts/UserContext";
import { useUser } from "@/contexts/UserContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { cn } from "@/libs/utils";
import { sendBooksToDeviceBatch } from "@/services/bookService";
import type { Book } from "@/types/book";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";
import { buildBookPermissionContext } from "@/utils/permissions";
import { DevicesSection } from "./DevicesSection";

export interface SendToDeviceFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Books to send. If not provided, uses selected books from context. */
  books?: Book[];
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback when books are successfully sent (to close parent menu). */
  onSuccess?: () => void;
  /** Callback to close parent menu (for Esc key handling). */
  onCloseParent?: () => void;
}

/**
 * Flyout menu for sending books to devices.
 *
 * Displays a submenu with default device option and other devices.
 * Positions itself dynamically (left or right) based on available space.
 * Follows SRP by handling only flyout menu display and interactions.
 * Uses IOC via hooks and callback props.
 *
 * Parameters
 * ----------
 * props : SendToDeviceFlyoutMenuProps
 *     Component props including open state, parent ref, book data, and callbacks.
 */
export function SendToDeviceFlyoutMenu({
  isOpen,
  parentItemRef,
  books: booksProp,
  onClose,
  onMouseEnter,
  onSuccess,
  onCloseParent,
}: SendToDeviceFlyoutMenuProps) {
  const [mounted, setMounted] = useState(false);
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [email, setEmail] = useState("");
  const emailInputRef = useRef<HTMLInputElement>(null);
  const { user, canPerformAction } = useUser();
  const { showDanger, showSuccess } = useGlobalMessages();

  // Get books from context if not provided via prop
  const { selectedBookIds, books: contextBooks } = useSelectedBooks();
  const books = useMemo(() => {
    if (booksProp) {
      return booksProp;
    }
    // Use selected books from context
    if (selectedBookIds.size === 0 || contextBooks.length === 0) {
      return [];
    }
    return contextBooks.filter((book) => selectedBookIds.has(book.id));
  }, [booksProp, selectedBookIds, contextBooks]);

  // Check permission - use first book for permission check
  // All books should have same permissions in practice
  const canSend =
    books.length > 0 &&
    books[0] !== undefined &&
    canPerformAction("books", "send", buildBookPermissionContext(books[0]));

  const { position, direction, menuRef } = useFlyoutPosition({
    isOpen,
    parentItemRef,
    mounted,
  });

  useEffect(() => {
    setMounted(true);
  }, []);

  // Focus email input when it appears
  useEffect(() => {
    if (showEmailInput && emailInputRef.current) {
      emailInputRef.current.focus();
    }
  }, [showEmailInput]);

  // Handle Esc key to close menus
  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        if (showEmailInput) {
          // If email input is shown, close both menus
          setShowEmailInput(false);
          setEmail("");
          onClose();
          onCloseParent?.();
        } else {
          // Otherwise, just close the flyout menu
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, showEmailInput, onClose, onCloseParent]);

  // Keep flyout open while pointer is within padded union of parent + flyout,
  // but close quickly once the pointer "rests" elsewhere to keep the UI snappy.
  useFlyoutIntent({
    isOpen,
    parentItemRef,
    menuRef,
    onClose,
    padding: 10,
    minMovementPx: 2,
    idleTimeMs: 20, // smaller value = snappier close; larger value = more forgiving, but sluggish
  });

  // Get default device and other devices
  const defaultDevice =
    user?.ereader_devices?.find((device) => device.is_default) || null;

  const otherDevices =
    user?.ereader_devices?.filter((device) => !device.is_default).slice(0, 5) ||
    [];

  /**
   * Handle mouse entering the flyout menu.
   */
  const handleFlyoutMouseEnter = useCallback(() => {
    onMouseEnter?.();
  }, [onMouseEnter]);

  /**
   * Handle sending books to default device.
   *
   * Fire-and-forget: sends all books in a single API call.
   * Backend creates a task for each book and enqueues them.
   * Sends one book per email (Kindle doesn't accept batches).
   */
  const handleSendToDefault = useCallback(() => {
    if (!defaultDevice || books.length === 0) {
      return;
    }

    const deviceName = defaultDevice.device_name || defaultDevice.email;
    const bookCount = books.length;

    // Fire-and-forget: send all books in one API call
    // Backend will create tasks for each book
    sendBooksToDeviceBatch(
      books.map((book) => book.id),
      {
        toEmail: defaultDevice.email,
      },
    )
      .then(() => {
        // Tasks enqueued successfully (background processing)
        if (bookCount === 1) {
          showSuccess(`Book queued for sending to ${deviceName}`);
        } else {
          showSuccess(
            `${bookCount} book${bookCount > 1 ? "s" : ""} queued for sending to ${deviceName}`,
          );
        }
      })
      .catch((error) => {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to send books";
        showDanger(errorMessage);
      });

    // Close UI immediately
    onClose();
    onSuccess?.();
  }, [books, defaultDevice, onClose, onSuccess, showDanger, showSuccess]);

  /**
   * Handle sending books to a specific device.
   *
   * Fire-and-forget: sends all books in a single API call.
   * Backend creates a task for each book and enqueues them.
   * Sends one book per email (Kindle doesn't accept batches).
   *
   * Parameters
   * ----------
   * device : EReaderDevice
   *     Device to send books to.
   */
  const handleSendToDevice = useCallback(
    (device: EReaderDevice) => {
      if (books.length === 0) {
        return;
      }

      const deviceName = device.device_name || device.email;
      const bookCount = books.length;

      // Fire-and-forget: send all books in one API call
      // Backend will create tasks for each book
      sendBooksToDeviceBatch(
        books.map((book) => book.id),
        {
          toEmail: device.email,
        },
      )
        .then(() => {
          // Tasks enqueued successfully (background processing)
          if (bookCount === 1) {
            showSuccess(`Book queued for sending to ${deviceName}`);
          } else {
            showSuccess(
              `${bookCount} book${bookCount > 1 ? "s" : ""} queued for sending to ${deviceName}`,
            );
          }
        })
        .catch((error) => {
          const errorMessage =
            error instanceof Error ? error.message : "Failed to send books";
          showDanger(errorMessage);
        });

      // Close UI immediately
      onClose();
      onSuccess?.();
    },
    [books, onClose, onSuccess, showDanger, showSuccess],
  );

  /**
   * Handle clicking "Send to email" menu item.
   */
  const handleSendToEmailClick = useCallback(() => {
    setShowEmailInput(true);
    setEmail("");
  }, []);

  /**
   * Handle submitting email input.
   *
   * Fire-and-forget: sends all books in a single API call.
   * Backend creates a task for each book and enqueues them.
   * Sends one book per email (Kindle doesn't accept batches).
   */
  const handleEmailSubmit = useCallback(() => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail || books.length === 0) {
      return;
    }

    const bookCount = books.length;

    // Fire-and-forget: send all books in one API call
    // Backend will create tasks for each book
    sendBooksToDeviceBatch(
      books.map((book) => book.id),
      {
        toEmail: trimmedEmail,
      },
    )
      .then(() => {
        // Tasks enqueued successfully (background processing)
        if (bookCount === 1) {
          showSuccess(`Book queued for sending to ${trimmedEmail}`);
        } else {
          showSuccess(
            `${bookCount} book${bookCount > 1 ? "s" : ""} queued for sending to ${trimmedEmail}`,
          );
        }
      })
      .catch((error) => {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to send books";
        showDanger(errorMessage);
      });

    // Close UI immediately
    setShowEmailInput(false);
    setEmail("");
    onClose();
    onSuccess?.();
  }, [books, email, onClose, onSuccess, showDanger, showSuccess]);

  /**
   * Handle Enter key in email input.
   */
  const handleEmailInputKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter") {
        e.preventDefault();
        e.stopPropagation();
        handleEmailSubmit();
      }
    },
    [handleEmailSubmit],
  );

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
        "min-w-[200px]",
      )}
      style={getFlyoutPositionStyle(position, direction)}
      role="menu"
      aria-label="Send to device"
      onMouseDown={(e) => e.stopPropagation()}
      onMouseEnter={handleFlyoutMouseEnter}
      data-keep-selection
    >
      <div className="py-1">
        {defaultDevice && (
          <DropdownMenuItem
            label={`Send to ${defaultDevice.device_name || defaultDevice.email}`}
            onClick={handleSendToDefault}
            disabled={!canSend}
          />
        )}
        <DevicesSection
          devices={otherDevices}
          onDeviceClick={handleSendToDevice}
          disabled={!canSend}
        />
        <hr className={cn("my-1 h-px border-0 bg-surface-tonal-a20")} />
        {showEmailInput ? (
          <div className="px-4 py-2.5">
            <input
              ref={emailInputRef}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={handleEmailInputKeyDown}
              placeholder="Enter email address"
              disabled={!canSend}
              className={cn(
                "w-full rounded px-3 py-1.5 text-sm",
                "border border-surface-tonal-a30 bg-surface-tonal-a10",
                "text-text-a0 placeholder:text-text-a40",
                "focus:border-surface-tonal-a50 focus:outline-none",
                "disabled:cursor-not-allowed disabled:opacity-50",
              )}
            />
          </div>
        ) : (
          <DropdownMenuItem
            label="Send to email"
            onClick={handleSendToEmailClick}
            disabled={!canSend}
          />
        )}
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
