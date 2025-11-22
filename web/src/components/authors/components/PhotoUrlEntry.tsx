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

import type React from "react";

interface PhotoUrlEntryProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

/**
 * Component for URL entry mode in photo upload.
 *
 * Follows SRP by handling only URL input UI and interactions.
 */
export function PhotoUrlEntry({
  value,
  onChange,
  onSubmit,
  onCancel,
}: PhotoUrlEntryProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      onSubmit();
    } else if (e.key === "Escape") {
      onCancel();
    }
  };

  return (
    <div className="flex w-full flex-col gap-1.5">
      <input
        className="h-[38px] w-full rounded-md border border-surface-a30 bg-surface-a10 px-2.5 py-1.5 text-sm text-text-a0 transition-colors focus:border-primary-a0 focus:bg-surface-a0 focus:outline-none"
        placeholder="Enter a url to upload an image from the web"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="flex justify-between text-text-a30 text-xs">
        <span>
          esc to{" "}
          <button
            type="button"
            className="cursor-pointer border-none bg-transparent p-0 text-primary-a0 transition-colors hover:text-primary-a10"
            onClick={onCancel}
          >
            cancel
          </button>
        </span>
        <span>
          enter to{" "}
          <button
            type="button"
            className="cursor-pointer border-none bg-transparent p-0 text-primary-a0 transition-colors hover:text-primary-a10"
            onClick={onSubmit}
          >
            upload
          </button>
        </span>
      </div>
    </div>
  );
}
