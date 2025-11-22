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

import { PhotoUrlEntry } from "./PhotoUrlEntry";

interface PhotoChooserBarProps {
  urlMode: boolean;
  urlValue: string;
  onUrlValueChange: (value: string) => void;
  onUrlSubmit: () => void;
  onUrlCancel: () => void;
  onChooseFile: () => void;
  onEnterUrlMode: () => void;
}

/**
 * Component for the photo chooser action bar.
 *
 * Follows SRP by handling only the chooser UI.
 */
export function PhotoChooserBar({
  urlMode,
  urlValue,
  onUrlValueChange,
  onUrlSubmit,
  onUrlCancel,
  onChooseFile,
  onEnterUrlMode,
}: PhotoChooserBarProps) {
  return (
    <div
      className="flex h-[65px] items-center gap-3.5 border-surface-a20 border-b text-text-a30"
      style={{
        margin: "-15px -20px 12px -20px",
        padding: "10px 20px",
        background:
          "repeating-linear-gradient(45deg, var(--color-surface-a10), var(--color-surface-a10) 10px, var(--color-surface-a0) 10px, var(--color-surface-a0) 20px)",
      }}
    >
      {urlMode ? (
        <PhotoUrlEntry
          value={urlValue}
          onChange={onUrlValueChange}
          onSubmit={onUrlSubmit}
          onCancel={onUrlCancel}
        />
      ) : (
        <>
          <button
            type="button"
            className="cursor-pointer border-none bg-transparent p-0 text-inherit text-primary-a0 transition-colors hover:text-primary-a10"
            onClick={onChooseFile}
          >
            choose an image
          </button>
          <span>·</span>
          <button
            type="button"
            className="cursor-pointer border-none bg-transparent p-0 text-inherit text-primary-a0 transition-colors hover:text-primary-a10"
            onClick={onEnterUrlMode}
          >
            enter a url
          </button>
        </>
      )}
    </div>
  );
}
