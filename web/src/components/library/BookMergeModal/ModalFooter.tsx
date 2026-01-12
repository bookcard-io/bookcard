// Copyright (C) 2026 knguyen and others
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

import { Button } from "@/components/forms/Button";

interface ModalFooterProps {
  onCancel: () => void;
  onDryRun: () => void;
  onMerge: () => void;
  disabled: boolean;
  isMerging: boolean;
}

export function ModalFooter({
  onCancel,
  onDryRun,
  onMerge,
  disabled,
  isMerging,
}: ModalFooterProps) {
  return (
    <div className="flex items-center justify-end gap-3 border-surface-a20 border-t p-6">
      <Button variant="secondary" onClick={onCancel} disabled={isMerging}>
        Cancel
      </Button>
      <Button
        variant="secondary"
        onClick={onDryRun}
        disabled={disabled || isMerging}
      >
        Dry run
      </Button>
      <Button onClick={onMerge} disabled={disabled || isMerging}>
        {isMerging && (
          <i className="pi pi-spin pi-spinner" aria-hidden="true" />
        )}
        {isMerging ? "Merging..." : "Merge books"}
      </Button>
    </div>
  );
}
