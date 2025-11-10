"use client";

import Image from "next/image";
import { useCallback } from "react";
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
          <Image
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
