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

import type { IconType } from "react-icons";
import { FaCheck, FaDownload, FaSearch } from "react-icons/fa";
import { cn } from "@/libs/utils";

interface StatusConfig {
  colorClass: string;
  icon?: IconType;
  animate?: boolean;
}

const DEFAULT_CONFIG: StatusConfig = {
  colorClass: "bg-surface-a20 text-text-a20",
};

const STATUS_CONFIGS: Record<string, StatusConfig> = {
  completed: {
    colorClass: "bg-success-a10/20 text-success-a10 border-success-a10/30",
    icon: FaCheck,
  },
  downloading: {
    colorClass: "bg-info-a10/20 text-info-a10 border-info-a10/30",
    icon: FaDownload,
  },
  wanted: {
    colorClass: "bg-danger-a10/20 text-danger-a10 border-danger-a10/30",
    icon: FaSearch,
  },
  searching: {
    colorClass: "bg-warning-a10/20 text-warning-a10 border-warning-a10/30",
    icon: FaSearch,
    animate: true,
  },
};

export function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIGS[status] ?? DEFAULT_CONFIG;
  const Icon = config.icon;

  return (
    <span
      className={cn(
        "flex items-center gap-1.5 rounded-md border px-2.5 py-1 font-bold text-xs uppercase tracking-wider",
        config.colorClass,
      )}
    >
      {Icon && (
        <Icon
          className={cn("text-[10px]", config.animate && "animate-pulse")}
        />
      )}
      {status}
    </span>
  );
}
