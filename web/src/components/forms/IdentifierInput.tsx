"use client";

import { type KeyboardEvent, useState } from "react";
import styles from "./IdentifierInput.module.scss";

export interface Identifier {
  type: string;
  val: string;
}

export interface IdentifierInputProps {
  /** Label text for the input. */
  label?: string;
  /** Current identifiers. */
  identifiers: Identifier[];
  /** Callback when identifiers change. */
  onChange: (identifiers: Identifier[]) => void;
  /** Error message to display. */
  error?: string;
  /** Helper text to display. */
  helperText?: string;
  /** Input ID for accessibility. */
  id?: string;
}

/**
 * Identifier input component for managing book identifiers (ISBN, DOI, etc.).
 *
 * Follows SRP by focusing solely on identifier management.
 * Uses controlled component pattern (IOC via props).
 */
export function IdentifierInput({
  label,
  identifiers,
  onChange,
  error,
  helperText,
  id = "identifier-input",
}: IdentifierInputProps) {
  const [typeValue, setTypeValue] = useState("isbn");
  const [valValue, setValValue] = useState("");

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addIdentifier();
    }
  };

  const addIdentifier = () => {
    const trimmed = valValue.trim();
    if (trimmed) {
      const newIdentifier: Identifier = {
        type: typeValue.trim() || "isbn",
        val: trimmed,
      };
      // Check for duplicates
      const isDuplicate = identifiers.some(
        (id) => id.type === newIdentifier.type && id.val === newIdentifier.val,
      );
      if (!isDuplicate) {
        onChange([...identifiers, newIdentifier]);
        setValValue("");
      }
    }
  };

  const removeIdentifier = (index: number) => {
    onChange(identifiers.filter((_, i) => i !== index));
  };

  return (
    <div className={styles.container}>
      {label && (
        <label htmlFor={`${id}-val`} className={styles.label}>
          {label}
        </label>
      )}
      <div className={styles.inputWrapper}>
        {identifiers.map((identifier, index) => (
          <div
            key={`${identifier.type}-${identifier.val}-${index}`}
            className={styles.identifierRow}
          >
            <span className={styles.identifierType}>{identifier.type}</span>
            <span className={styles.identifierVal}>{identifier.val}</span>
            <button
              type="button"
              className={styles.removeButton}
              onClick={() => removeIdentifier(index)}
              aria-label={`Remove ${identifier.type} ${identifier.val}`}
            >
              ×
            </button>
          </div>
        ))}
        <div className={styles.addRow}>
          <select
            id={`${id}-type`}
            className={styles.typeSelect}
            value={typeValue}
            onChange={(e) => setTypeValue(e.target.value)}
          >
            <option value="isbn">ISBN</option>
            <option value="doi">DOI</option>
            <option value="asin">ASIN</option>
            <option value="goodreads">Goodreads</option>
            <option value="google">Google Books</option>
            <option value="amazon">Amazon</option>
            <option value="other">Other</option>
          </select>
          <input
            id={`${id}-val`}
            type="text"
            className={`${styles.valInput} ${error ? styles.inputError : ""}`}
            value={valValue}
            onChange={(e) => setValValue(e.target.value)}
            onKeyDown={handleKeyDown}
            onBlur={addIdentifier}
            placeholder="Enter identifier value..."
            aria-invalid={error ? "true" : "false"}
            aria-describedby={
              error || helperText
                ? `${id}-${error ? "error" : "helper"}`
                : undefined
            }
          />
        </div>
      </div>
      {error && (
        <span id={`${id}-error`} className={styles.error} role="alert">
          {error}
        </span>
      )}
      {helperText && !error && (
        <span id={`${id}-helper`} className={styles.helperText}>
          {helperText}
        </span>
      )}
    </div>
  );
}
