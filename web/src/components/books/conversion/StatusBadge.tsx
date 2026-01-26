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

import { STATUS_BADGE_CLASS_BY_STATUS } from "@/constants/conversion";

export interface StatusBadgeProps {
  /** Human-readable status. */
  status: string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const normalizedStatus = status.trim().toLowerCase();
  const className =
    STATUS_BADGE_CLASS_BY_STATUS[normalizedStatus] ??
    "bg-gray-500/20 text-gray-400";

  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs ${className}`}>
      {status}
    </span>
  );
}
