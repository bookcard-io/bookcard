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

import { useRef, useState } from "react";
import { AddColumnRightOutline } from "@/icons/AddColumnRightOutline";
import { cn } from "@/libs/utils";
import { createEnterSpaceHandler } from "@/utils/keyboard";
import { ListColumnSelector } from "./ListColumnSelector";

export interface ColumnSelectorButtonProps {
  /** Whether the button should be visible. */
  visible?: boolean;
}

/**
 * Column selector button component for list view.
 *
 * Toggles column selector dropdown.
 * Follows SRP by handling only button UI and state.
 * Uses IOC via component composition.
 */
export function ColumnSelectorButton({
  visible = true,
}: ColumnSelectorButtonProps) {
  const [isOpen, setIsOpen] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);

  const handleToggle = () => {
    setIsOpen((prev) => !prev);
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  const handleKeyDown = createEnterSpaceHandler(handleToggle);

  if (!visible) {
    return null;
  }

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        className={cn(
          "btn-tonal flex h-9 items-center justify-center gap-2 px-3",
          isOpen && "bg-surface-a10",
        )}
        aria-label="Select columns"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <AddColumnRightOutline className="h-5 w-5" />
        <span>Columns</span>
      </button>
      <ListColumnSelector
        isOpen={isOpen}
        onClose={handleClose}
        buttonRef={buttonRef}
      />
    </div>
  );
}
