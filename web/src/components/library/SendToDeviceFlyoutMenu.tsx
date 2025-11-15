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

import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { DropdownMenuItem } from "@/components/common/DropdownMenuItem";
import type { EReaderDevice } from "@/contexts/UserContext";
import { useUser } from "@/contexts/UserContext";
import { useFlyoutIntent } from "@/hooks/useFlyoutIntent";
import { useFlyoutPosition } from "@/hooks/useFlyoutPosition";
import { cn } from "@/libs/utils";
import { sendBookToDevice } from "@/services/bookService";
import { getFlyoutPositionStyle } from "@/utils/flyoutPositionStyle";
import { DevicesSection } from "./DevicesSection";

export interface SendToDeviceFlyoutMenuProps {
  /** Whether the flyout menu is open. */
  isOpen: boolean;
  /** Reference to the parent menu item element. */
  parentItemRef: React.RefObject<HTMLElement | null>;
  /** Book ID to send. */
  bookId: number;
  /** Callback when menu should be closed. */
  onClose: () => void;
  /** Callback when mouse enters the flyout (to keep parent menu item hovered). */
  onMouseEnter?: () => void;
  /** Callback when book is successfully sent (to close parent menu). */
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
 *     Component props including open state, parent ref, book ID, and callbacks.
 */
export function SendToDeviceFlyoutMenu({
  isOpen,
  parentItemRef,
  bookId,
  onClose,
  onMouseEnter,
  onSuccess,
  onCloseParent,
}: SendToDeviceFlyoutMenuProps) {
  const [mounted, setMounted] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [showEmailInput, setShowEmailInput] = useState(false);
  const [email, setEmail] = useState("");
  const emailInputRef = useRef<HTMLInputElement>(null);
  const { user } = useUser();

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
   * Handle sending book to default device.
   */
  const handleSendToDefault = useCallback(async () => {
    if (!defaultDevice) {
      return;
    }
    try {
      setIsSending(true);
      await sendBookToDevice(bookId, {
        toEmail: defaultDevice.email,
      });
      onClose();
      onSuccess?.();
    } catch (error) {
      console.error("Failed to send book:", error);
      alert(error instanceof Error ? error.message : "Failed to send book");
    } finally {
      setIsSending(false);
    }
  }, [bookId, defaultDevice, onClose, onSuccess]);

  /**
   * Handle sending book to a specific device.
   *
   * Parameters
   * ----------
   * device : EReaderDevice
   *     Device to send book to.
   */
  const handleSendToDevice = useCallback(
    async (device: EReaderDevice) => {
      try {
        setIsSending(true);
        await sendBookToDevice(bookId, {
          toEmail: device.email,
        });
        onClose();
        onSuccess?.();
      } catch (error) {
        console.error("Failed to send book:", error);
        alert(error instanceof Error ? error.message : "Failed to send book");
      } finally {
        setIsSending(false);
      }
    },
    [bookId, onClose, onSuccess],
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
   */
  const handleEmailSubmit = useCallback(async () => {
    const trimmedEmail = email.trim();
    if (!trimmedEmail) {
      return;
    }

    try {
      setIsSending(true);
      await sendBookToDevice(bookId, {
        toEmail: trimmedEmail,
      });
      setShowEmailInput(false);
      setEmail("");
      onClose();
      onSuccess?.();
    } catch (error) {
      console.error("Failed to send book:", error);
      alert(error instanceof Error ? error.message : "Failed to send book");
    } finally {
      setIsSending(false);
    }
  }, [bookId, email, onClose, onSuccess]);

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
    >
      <div className="py-1">
        {defaultDevice && (
          <DropdownMenuItem
            label={`Send to ${defaultDevice.device_name || defaultDevice.email}`}
            onClick={handleSendToDefault}
            disabled={isSending}
          />
        )}
        <DevicesSection
          devices={otherDevices}
          onDeviceClick={handleSendToDevice}
          disabled={isSending}
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
              disabled={isSending}
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
            disabled={isSending}
          />
        )}
      </div>
    </div>
  );

  return createPortal(menuContent, document.body);
}
