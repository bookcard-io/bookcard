"use client";

import { useState } from "react";
import { useBlurAfterClick } from "../BlurAfterClickContext";

/**
 * Default delete files from drive configuration component.
 *
 * Manages the default state for "delete files from drive" checkbox.
 * Follows SRP by handling only delete files preference.
 */
export function DefaultDeleteFilesFromDriveConfiguration() {
  const [deleteFilesFromDrive, setDeleteFilesFromDrive] = useState(false);
  const { onBlurChange } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">
        Default Delete Files from Drive
      </div>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="checkbox"
          checked={deleteFilesFromDrive}
          onChange={onBlurChange(() =>
            setDeleteFilesFromDrive(!deleteFilesFromDrive),
          )}
          className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
        />
        <span className="text-base text-text-a0">
          Delete files from filesystem by default when deleting books
        </span>
      </label>
    </div>
  );
}
