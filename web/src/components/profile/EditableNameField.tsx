"use client";

import { useState } from "react";

interface EditableTextFieldProps {
  /**
   * Current value to display and edit.
   */
  currentValue: string | null | undefined;
  /**
   * Callback invoked when the user saves the edited value.
   *
   * Parameters
   * ----------
   * value : string
   *     The new value entered by the user.
   */
  onSave?: (value: string) => void;
  /**
   * Placeholder text for the input field.
   */
  placeholder?: string;
  /**
   * Label for the edit button (for accessibility).
   */
  editLabel?: string;
  /**
   * Whether the field can be empty (shows "Not set" if empty).
   */
  allowEmpty?: boolean;
}

/**
 * Editable text field component.
 *
 * Allows users to edit text values inline with edit/save/cancel functionality.
 * Generic component that can be used for any editable text field (e.g., name, username).
 * Follows SRP by handling only text editing UI.
 */
export function EditableTextField({
  currentValue,
  onSave,
  placeholder = "Enter value",
  editLabel = "Edit",
  allowEmpty = true,
}: EditableTextFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [value, setValue] = useState(currentValue || "");

  const handleSave = () => {
    if (onSave) {
      onSave(value);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setValue(currentValue || "");
    setIsEditing(false);
  };

  if (!isEditing) {
    return (
      <div className="flex items-center gap-2">
        <div className="text-text-a0">
          {currentValue ? (
            currentValue
          ) : allowEmpty ? (
            <span className="text-text-a30">Not set</span>
          ) : (
            ""
          )}
        </div>
        <button
          type="button"
          onClick={() => setIsEditing(true)}
          className="rounded border border-surface-a20 bg-surface-tonal-a10 px-2 py-1 font-medium text-text-a0 text-xs transition-colors duration-200 hover:bg-surface-tonal-a20"
          aria-label={editLabel}
        >
          <i className="pi pi-pencil" aria-hidden="true" />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        className="rounded border border-surface-a20 bg-surface-tonal-a10 px-3 py-2 text-text-a0 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary-a0"
        placeholder={placeholder}
      />
      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSave}
          className="rounded border-0 bg-primary-a0 px-3 py-1.5 font-medium text-text-a0 text-xs transition-colors duration-200 hover:bg-primary-a10"
        >
          Save
        </button>
        <button
          type="button"
          onClick={handleCancel}
          className="rounded border border-surface-a20 bg-surface-tonal-a10 px-3 py-1.5 font-medium text-text-a0 text-xs transition-colors duration-200 hover:bg-surface-tonal-a20"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

/**
 * Editable name field component.
 *
 * Convenience wrapper for EditableTextField specifically for full name editing.
 * Maintains backward compatibility with existing code.
 */
export function EditableNameField({
  currentName,
  onSave,
}: {
  currentName: string | null | undefined;
  onSave?: (name: string) => void;
}) {
  return (
    <EditableTextField
      currentValue={currentName}
      onSave={onSave}
      placeholder="Enter your full name"
      editLabel="Edit name"
    />
  );
}
