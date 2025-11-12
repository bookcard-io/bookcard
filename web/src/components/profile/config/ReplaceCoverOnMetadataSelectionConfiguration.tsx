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

import { useBooleanSetting } from "@/hooks/useBooleanSetting";
import { useBlurAfterClick } from "../BlurAfterClickContext";

const SETTING_KEY = "replace_cover_on_metadata_selection";
const DEFAULT_VALUE = false;

/**
 * Replace cover on metadata selection configuration component.
 *
 * Manages the preference to automatically replace the existing cover
 * with the cover from the selected metadata item.
 */
export function ReplaceCoverOnMetadataSelectionConfiguration() {
  const { value, setValue } = useBooleanSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });
  const { onBlurChange } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">
        Replace Cover on Metadata Selection
      </div>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="checkbox"
          checked={value}
          onChange={onBlurChange(() => setValue(!value))}
          className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
        />
        <span className="text-base text-text-a0">
          When selecting a metadata result, also replace the current cover with
          the picked cover
        </span>
      </label>
    </div>
  );
}
