"use client";

import { useCallback, useEffect, useState } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { type Library, LibraryList } from "./LibraryList";
import styles from "./LibraryManagement.module.scss";
import { PathInputWithSuggestions } from "./PathInputWithSuggestions";

export function LibraryManagement() {
  const { refresh: refreshActiveLibrary } = useActiveLibrary();
  const [libraries, setLibraries] = useState<Library[]>([]);
  const [newPath, setNewPath] = useState("");
  const [newName, setNewName] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingLibraryId, setDeletingLibraryId] = useState<number | null>(
    null,
  );

  const fetchLibraries = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await fetch("/api/admin/libraries", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load libraries");
      }

      const data = await response.json();
      setLibraries(data);
    } catch {
      setError("Failed to load libraries");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshLibraries = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch("/api/admin/libraries", {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error("Failed to load libraries");
      }

      const data = await response.json();
      setLibraries(data);
    } catch {
      setError("Failed to refresh libraries");
    }
  }, []);

  useEffect(() => {
    void fetchLibraries();
  }, [fetchLibraries]);

  const handleAdd = async () => {
    const trimmedPath = newPath.trim();
    const trimmedName = newName.trim();
    if (!trimmedPath) {
      setError("Path is required");
      return;
    }

    // Generate default name if not provided
    let libraryName = trimmedName;
    if (!libraryName) {
      const myLibraryPattern = /^My Library(?: \((\d+)\))?$/;
      const hasBaseName = libraries.some((lib) => lib.name === "My Library");
      const numberedNames = libraries
        .map((lib) => {
          const match = lib.name.match(myLibraryPattern);
          return match?.[1] ? parseInt(match[1], 10) : null;
        })
        .filter((num): num is number => num !== null);

      if (!hasBaseName && numberedNames.length === 0) {
        libraryName = "My Library";
      } else {
        // Find the next available number
        const maxNumber =
          numberedNames.length > 0 ? Math.max(...numberedNames) : 0;
        libraryName = `My Library (${maxNumber + 1})`;
      }
    }

    setIsBusy(true);
    setError(null);
    try {
      const response = await fetch("/api/admin/libraries", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          name: libraryName,
          calibre_db_path: trimmedPath,
          calibre_db_file: "metadata.db",
          is_active: false,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to add library");
      }

      setNewPath("");
      setNewName("");
      await refreshLibraries();
      await refreshActiveLibrary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add library");
    } finally {
      setIsBusy(false);
    }
  };

  const handleToggle = async (library: Library) => {
    setError(null);
    try {
      // Toggle: if already active, deactivate; otherwise activate
      if (library.is_active) {
        // Deactivate by setting is_active to false
        const response = await fetch(`/api/admin/libraries/${library.id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            is_active: false,
          }),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Failed to deactivate library");
        }
      } else {
        // Activate using the activate endpoint
        const response = await fetch(
          `/api/admin/libraries/${library.id}/activate`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
          },
        );

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || "Failed to activate library");
        }
      }

      await refreshLibraries();
      await refreshActiveLibrary();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to toggle library activation state",
      );
    }
  };

  const handleDelete = async (id: number) => {
    setDeletingLibraryId(id);
    setIsBusy(true);
    setError(null);
    try {
      const response = await fetch(`/api/admin/libraries/${id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to delete library");
      }

      await refreshLibraries();
      await refreshActiveLibrary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete library");
    } finally {
      setIsBusy(false);
      setDeletingLibraryId(null);
    }
  };

  if (isLoading) {
    return <div className={styles.loading}>Loading libraries...</div>;
  }

  return (
    <div className={styles.container}>
      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.addSection}>
        <div className={styles.inputGroup}>
          <input
            type="text"
            value={newName}
            onChange={(e) => {
              setNewName(e.target.value);
              setError(null);
            }}
            placeholder="Library name (optional)"
            className={styles.nameInput}
            disabled={isBusy}
          />
          <PathInputWithSuggestions
            value={newPath}
            onChange={(v) => {
              setNewPath(v);
              setError(null);
            }}
            onSubmit={handleAdd}
            busy={isBusy}
          />
          <button
            type="button"
            onClick={handleAdd}
            disabled={!newPath.trim() || isBusy}
            className={styles.addButton}
          >
            Add
          </button>
        </div>
      </div>

      <LibraryList
        libraries={libraries}
        onToggle={handleToggle}
        onDelete={handleDelete}
        deletingLibraryId={deletingLibraryId}
      />
    </div>
  );
}
