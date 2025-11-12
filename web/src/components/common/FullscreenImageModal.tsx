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

import { useCallback } from "react";
import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import { useKeyboardNavigation } from "@/hooks/useKeyboardNavigation";
import { useModal } from "@/hooks/useModal";
import styles from "./FullscreenImageModal.module.scss";

export interface FullscreenImageModalProps {
  /** Image source URL. */
  src: string;
  /** Alternative text describing the image. */
  alt: string;
  /** Whether the modal is open. */
  isOpen: boolean;
  /** Called when the modal should be closed. */
  onClose: () => void;
}

/**
 * Fullscreen image modal.
 *
 * Displays an image in a fullscreen overlay and closes on click or Escape.
 * Single-responsibility: render and manage a fullscreen image dialog.
 */
export function FullscreenImageModal({
  src,
  alt,
  isOpen,
  onClose,
}: FullscreenImageModalProps) {
  useModal(isOpen);

  useKeyboardNavigation({
    onEscape: onClose,
    enabled: isOpen,
  });

  const handleOverlayClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (e.target === e.currentTarget) {
        onClose();
      }
    },
    [onClose],
  );

  if (!isOpen) {
    return null;
  }

  return (
    /* biome-ignore lint/a11y/noStaticElementInteractions: modal pattern */
    <div
      className={styles.overlay}
      onClick={handleOverlayClick}
      role="presentation"
    >
      <div
        className={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-label="Fullscreen image"
      >
        <button
          type="button"
          className={styles.buttonArea}
          aria-label="Close fullscreen image"
          onClick={onClose}
        >
          <span className={styles.srOnly}>Click anywhere to close</span>
          <ImageWithLoading
            src={src}
            alt={alt}
            fill={false}
            width={1600}
            height={1600}
            className={styles.image}
            unoptimized
          />
        </button>
      </div>
    </div>
  );
}
