"use client";

import { cn } from "@/libs/utils";

export interface Library {
  id: number;
  name: string;
  calibre_db_path: string;
  calibre_db_file: string;
  calibre_uuid: string | null;
  use_split_library: boolean;
  split_library_dir: string | null;
  auto_reconnect: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

type Props = {
  libraries: Library[];
  onToggle: (library: Library) => void;
  onDelete: (id: number) => void;
  deletingLibraryId: number | null;
};

export function LibraryList({
  libraries,
  onToggle,
  onDelete,
  deletingLibraryId,
}: Props) {
  return (
    <div className="flex flex-col gap-2">
      {libraries.map((lib) => (
        <div
          key={lib.id}
          className="flex items-center gap-3 rounded-md border border-[var(--color-surface-a20)] bg-[var(--color-surface-a10)] p-3"
        >
          <div className="flex flex-1 items-center gap-3">
            <input
              type="checkbox"
              checked={lib.is_active}
              onChange={() => onToggle(lib)}
              className="h-[18px] w-[18px] cursor-pointer accent-[var(--color-primary-a0)]"
            />
            <div className="flex flex-1 flex-col gap-1">
              <div
                className={cn(
                  "font-medium text-sm",
                  lib.is_active
                    ? "text-[var(--color-primary-a0)]"
                    : "text-[var(--color-text-a0)]",
                )}
              >
                {lib.name}
              </div>
              <div className="break-all text-[var(--color-text-a30)] text-xs">
                {lib.calibre_db_path}
              </div>
              {lib.updated_at && (
                <div className="text-[11px] text-[var(--color-text-a40)]">
                  Last updated: {new Date(lib.updated_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => onDelete(lib.id)}
            disabled={deletingLibraryId === lib.id}
            className={cn(
              "cursor-pointer rounded-md border border-[var(--color-danger-a20)] bg-transparent px-3 py-1.5 font-medium text-[var(--color-danger-a0)] text-xs transition-colors duration-150",
              deletingLibraryId === lib.id
                ? "cursor-not-allowed border-[var(--color-danger-a30)] text-[var(--color-danger-a30)] opacity-60"
                : "hover:bg-[var(--color-danger-a20)] hover:text-[var(--color-danger-a0)]",
            )}
          >
            Remove
          </button>
        </div>
      ))}
      {libraries.length === 0 && (
        <div className="p-6 text-center text-[var(--color-text-a30)] text-sm italic">
          No libraries configured yet.
        </div>
      )}
      {libraries.length > 0 && !libraries.some((lib) => lib.is_active) && (
        <div className="p-6 text-center text-[var(--color-text-a30)] text-sm italic">
          Please activate a library to begin using the app.
        </div>
      )}
    </div>
  );
}
