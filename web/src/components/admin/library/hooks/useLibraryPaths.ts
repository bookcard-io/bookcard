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

import { useCallback, useEffect, useState } from "react";

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

export function useLibraryPaths() {
  const [paths, setPaths] = useState<Library[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingPathId, setDeletingPathId] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/admin/libraries", {
        cache: "no-store",
      });
      if (!response.ok) throw new Error("failed_to_load_paths");
      const data = (await response.json()) as Library[];
      setPaths(Array.isArray(data) ? data : []);
    } catch {
      setError("Failed to load libraries");
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const addPath = useCallback(
    async (
      name: string,
      calibre_db_path: string,
      setAsActive: boolean = false,
    ): Promise<boolean> => {
      const trimmed = calibre_db_path.trim();
      if (!trimmed || !name.trim()) return false;
      setBusy(true);
      setError(null);
      try {
        const response = await fetch("/api/admin/libraries", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name.trim(),
            calibre_db_path: trimmed,
            set_as_active: setAsActive,
          }),
        });
        if (!response.ok) throw new Error("failed_to_add_path");
        await refresh();
        return true;
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : String(e);
        setError(message || "Unable to add library");
        return false;
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  const deletePath = useCallback(
    async (id: number) => {
      setDeletingPathId(id);
      setBusy(true);
      setError(null);
      try {
        const response = await fetch(`/api/admin/libraries/${id}`, {
          method: "DELETE",
        });
        if (!response.ok) throw new Error("failed_to_delete_path");
        await refresh();
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : String(e);
        setError(message || "Unable to delete library");
      } finally {
        setBusy(false);
        setDeletingPathId(null);
      }
    },
    [refresh],
  );

  const activateLibrary = useCallback(
    async (id: number) => {
      setBusy(true);
      setError(null);
      try {
        const response = await fetch(`/api/admin/libraries/${id}/activate`, {
          method: "POST",
        });
        if (!response.ok) throw new Error("failed_to_activate_library");
        await refresh();
      } catch (e: unknown) {
        const message = e instanceof Error ? e.message : String(e);
        setError(message || "Unable to activate library");
      } finally {
        setBusy(false);
      }
    },
    [refresh],
  );

  return {
    paths,
    refresh,
    addPath,
    deletePath,
    activateLibrary,
    busy,
    error,
    setError,
    deletingPathId,
  } as const;
}
