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
import { DefaultDeleteFilesFromDriveConfiguration } from "./DefaultDeleteFilesFromDriveConfiguration";
import { DeleteWarningConfiguration } from "./DeleteWarningConfiguration";

/**
 * Delete settings group component.
 *
 * Wraps delete warning and delete files from drive configurations.
 * Shows a warning when delete warning is disabled and delete files is enabled.
 * Follows SRP by handling only the grouping and warning logic.
 * Follows SOC by separating warning display from individual settings.
 */
export function DeleteSettingsGroup() {
  const { value: isWarningEnabled } = useBooleanSetting({
    key: "always_warn_on_delete",
    defaultValue: true,
  });
  const { value: isDeleteFilesEnabled } = useBooleanSetting({
    key: "default_delete_files_from_drive",
    defaultValue: false,
  });

  const shouldShowWarning = !isWarningEnabled && isDeleteFilesEnabled;

  return (
    <div className="flex flex-col gap-6">
      {shouldShowWarning && (
        <div className="flex items-start gap-3 rounded-lg border border-[var(--color-warning-a0)] bg-[var(--color-warning-a0)]/20 p-4">
          <i
            className="pi pi-exclamation-triangle mt-0.5 text-warning-a10"
            aria-hidden="true"
          />
          <div className="flex flex-col gap-1">
            <div className="font-medium text-sm text-warning-a10">
              Warning: No confirmation dialog
            </div>
            <div className="text-sm text-warning-a20">
              You will not be warned before deleting books. Deleted books cannot
              be recovered.
            </div>
          </div>
        </div>
      )}
      <DeleteWarningConfiguration />
      <DefaultDeleteFilesFromDriveConfiguration />
    </div>
  );
}
