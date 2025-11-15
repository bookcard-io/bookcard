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

import { useCallback, useMemo } from "react";
import { Ereader } from "@/icons/EReader";
import { Kindle } from "@/icons/Kindle";
import { KoboBooks } from "@/icons/Kobo";
import { Nook } from "@/icons/Nook";
import { cn } from "@/libs/utils";
import type { EReaderDevice } from "./hooks/useUserProfile";

export interface DeviceCardProps {
  /** Device data to display. */
  device: EReaderDevice;
  /** Callback when device is edited (clicked on icon). */
  onEdit?: (device: EReaderDevice) => void;
  /** Callback when device is deleted. */
  onDelete?: (deviceId: number) => Promise<void>;
}

/**
 * Device card component for displaying a single device in the grid.
 *
 * Displays device icon, name, email, and optional default indicator.
 * Follows SRP by focusing solely on device display.
 * Follows DRY by reusing ShelfCard styling pattern.
 *
 * Parameters
 * ----------
 * props : DeviceCardProps
 *     Component props including device data.
 */
export function DeviceCard({ device, onEdit, onDelete }: DeviceCardProps) {
  const DeviceIcon = useMemo(() => {
    switch (device.device_type?.toLowerCase()) {
      case "kindle":
        return Kindle;
      case "kobo":
        return KoboBooks;
      case "nook":
        return Nook;
      default:
        return Ereader;
    }
  }, [device.device_type]);

  const handleEdit = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onEdit) {
        onEdit(device);
      }
    },
    [device, onEdit],
  );

  const handleDelete = useCallback(
    async (e: React.MouseEvent) => {
      e.stopPropagation();
      if (onDelete) {
        await onDelete(device.id);
      }
    },
    [device.id, onDelete],
  );

  return (
    <div
      className={cn(
        /* Layout */
        "group flex flex-col overflow-hidden rounded text-left",
        "w-full max-w-[175px] p-0",
        /* Border & background */
        "border-2 border-transparent",
        "bg-gradient-to-b from-surface-a0 to-surface-a10",
        /* Interactions */
        "cursor-pointer",
        "transition-[transform,box-shadow,border-color] duration-200 ease-out",
        "hover:-translate-y-0.5 hover:shadow-card-hover",
        /* Focus states */
        "focus-visible:outline-2 focus-visible:outline-primary-a0 focus-visible:outline-offset-2",
        "focus:not-focus-visible:outline-none focus:outline-none",
      )}
    >
      <div
        className={cn(
          /* Layout */
          "relative aspect-square w-full overflow-hidden",
        )}
      >
        {device.is_default && (
          <div
            className={cn(
              /* Position */
              "absolute top-2 right-2 z-10",
              /* Layout */
              "flex items-center justify-center",
            )}
            title="Default device"
          >
            <i
              className={cn("pi pi-asterisk text-sm")}
              style={{ color: "var(--color-success-a20)" }}
              aria-hidden="true"
            />
          </div>
        )}
        <button
          type="button"
          onClick={handleEdit}
          className={cn(
            /* Layout */
            "flex h-full w-full items-center justify-center",
            /* Background */
            "bg-gradient-to-br from-surface-a20 to-surface-a10",
            /* Interactions */
            "cursor-pointer transition-opacity duration-200",
            "hover:opacity-80",
            /* Focus states */
            "focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2",
          )}
          aria-label="Edit device"
          title="Edit device"
        >
          <DeviceIcon className={cn("h-85 w-85 text-text-a30")} />
        </button>
        {onDelete && (
          <button
            type="button"
            onClick={handleDelete}
            className={cn(
              /* Position */
              "absolute right-2 bottom-2 z-10",
              /* Layout */
              "flex h-6 w-6 items-center justify-center rounded",
              /* Background */
              "bg-surface-a20/80 backdrop-blur-sm",
              /* Interactions */
              "transition-colors duration-200",
              "hover:bg-surface-a30",
              /* Focus states */
              "focus:outline-2 focus:outline-primary-a0 focus:outline-offset-2",
            )}
            aria-label="Delete device"
            title="Delete device"
          >
            <i
              className={cn("pi pi-trash text-xs")}
              style={{ color: "var(--color-danger-a20)" }}
              aria-hidden="true"
            />
          </button>
        )}
      </div>
      <div
        className={cn(
          /* Layout */
          "relative flex min-h-12 flex-col justify-end gap-0.5",
          /* Background */
          "bg-surface-a10 p-2",
          /* Cursor */
          "cursor-default",
        )}
      >
        <h3
          className={cn(
            /* Layout */
            "m-0 line-clamp-2 pr-6",
            /* Typography */
            "font-[500] text-text-a0 text-xs leading-[1.2]",
            /* Cursor */
            "cursor-text",
          )}
          title={device.device_name || undefined}
        >
          {device.device_name || <span className={cn("text-text-a30")}>—</span>}
        </h3>
        <p
          className={cn(
            /* Layout */
            "m-0 line-clamp-1 pr-6",
            /* Typography */
            "text-[0.625rem] text-text-a20 leading-[1.2]",
            /* Cursor */
            "cursor-text",
          )}
          title={device.email}
        >
          {device.email}
        </p>
      </div>
    </div>
  );
}
