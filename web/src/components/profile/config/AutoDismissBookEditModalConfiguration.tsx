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

const SETTING_KEY = "auto_dismiss_book_edit_modal";
const DEFAULT_VALUE = true;

/**
 * Auto-dismiss book edit modal configuration component.
 *
 * Manages the "Automatically dismiss modal on save" preference.
 * Follows SRP by handling only auto-dismiss preference.
 * Follows IOC by using useBooleanSetting hook for persistence.
 */
export function AutoDismissBookEditModalConfiguration() {
  const { value, setValue } = useBooleanSetting({
    key: SETTING_KEY,
    defaultValue: DEFAULT_VALUE,
  });
  const { onBlurChange } = useBlurAfterClick();

  return (
    <div className="flex flex-col gap-3">
      <div className="font-medium text-sm text-text-a20">
        Auto-dismiss Book Edit Modal
      </div>
      <label className="flex cursor-pointer items-center gap-2">
        <input
          type="checkbox"
          checked={value}
          onChange={onBlurChange(() => setValue(!value))}
          className="h-4 w-4 cursor-pointer rounded border-surface-a20 text-primary-a0 accent-[var(--color-primary-a0)] focus:ring-2 focus:ring-primary-a0"
        />
        <span className="text-base text-text-a0">
          Automatically close the book edit modal after saving changes
        </span>
      </label>
    </div>
  );
}
