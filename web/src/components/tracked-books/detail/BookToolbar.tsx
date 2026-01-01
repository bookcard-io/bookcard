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

import { FaHistory, FaPenFancy, FaSearch, FaTrash } from "react-icons/fa";
import { IconButton } from "@/components/common/IconButton";
import { Button } from "@/components/forms/Button";

interface BookToolbarProps {
  onSearchClick: () => void;
  onEditClick: () => void;
  onManualImportClick: () => void;
  onDeleteClick: () => void;
}

export function BookToolbar({
  onSearchClick,
  onEditClick,
  onManualImportClick,
  onDeleteClick,
}: BookToolbarProps) {
  return (
    <div className="mt-6 flex flex-wrap items-center gap-4">
      <Button variant="primary" size="small" onClick={onSearchClick}>
        <FaSearch />
        Interactive Search
      </Button>

      <div className="flex items-center gap-2">
        <IconButton icon={FaPenFancy} tooltip="Edit" onClick={onEditClick} />
        <IconButton
          icon={FaHistory}
          tooltip="Manual Import"
          onClick={onManualImportClick}
        />
        <IconButton
          icon={FaTrash}
          tooltip="Delete"
          onClick={onDeleteClick}
          variant="danger"
        />
      </div>
    </div>
  );
}
