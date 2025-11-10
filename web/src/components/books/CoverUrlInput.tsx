"use client";

import { TextInput } from "@/components/forms/TextInput";
import styles from "./BookEditModal.module.scss";

export interface CoverUrlInputProps {
  /** Input value. */
  value: string;
  /** Whether input is disabled. */
  disabled?: boolean;
  /** Error message to display. */
  error?: string | null;
  /** Ref for the input element. */
  inputRef: React.RefObject<HTMLInputElement>;
  /** Handler for value changes. */
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  /** Handler for keyboard events. */
  onKeyDown: (e: React.KeyboardEvent<HTMLInputElement>) => void;
}

/**
 * Cover URL input component.
 *
 * Displays an input field for entering a cover image URL.
 * Follows SRP by focusing solely on URL input presentation.
 *
 * Parameters
 * ----------
 * props : CoverUrlInputProps
 *     Component props including value, handlers, and state.
 */
export function CoverUrlInput({
  value,
  disabled,
  error,
  inputRef,
  onChange,
  onKeyDown,
}: CoverUrlInputProps) {
  return (
    <div className={styles.urlInputContainer}>
      <TextInput
        ref={inputRef}
        id="cover-url-input"
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        placeholder="Paste URL and press Enter"
        disabled={disabled}
        error={error || undefined}
        autoFocus
      />
    </div>
  );
}
