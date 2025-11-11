"use client";

import { useState } from "react";

interface EditableNameFieldProps {
  currentName: string | null | undefined;
  onSave?: (name: string) => void;
}

/**
 * Editable name field component.
 *
 * Allows users to edit their full name inline.
 * Currently a no-op implementation as backend is not wired to accept full_name.
 * Follows SRP by handling only name editing UI.
 */
export function EditableNameField({
  currentName,
  onSave,
}: EditableNameFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [name, setName] = useState(currentName || "");

  const handleSave = () => {
    // No-op for now - backend not wired to accept full_name
    if (onSave) {
      onSave(name);
    }
    setIsEditing(false);
  };

  const handleCancel = () => {
    setName(currentName || "");
    setIsEditing(false);
  };

  if (!isEditing) {
    return (
      <div className="flex items-center gap-2">
        <div className="text-text-a0">
          {currentName ?? <span className="text-text-a30">Not set</span>}
        </div>
        <button
          type="button"
          onClick={() => setIsEditing(true)}
          className="rounded border border-surface-a20 bg-surface-tonal-a10 px-2 py-1 font-medium text-text-a0 text-xs transition-colors duration-200 hover:bg-surface-tonal-a20"
          aria-label="Edit name"
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
        value={name}
        onChange={(e) => setName(e.target.value)}
        className="rounded border border-surface-a20 bg-surface-tonal-a10 px-3 py-2 text-text-a0 focus:border-transparent focus:outline-none focus:ring-2 focus:ring-primary-a0"
        placeholder="Enter your full name"
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
