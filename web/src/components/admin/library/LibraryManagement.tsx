"use client";

import { useCallback, useState } from "react";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";
import { useLibraryManagement } from "./hooks/useLibraryManagement";
import { LibraryList } from "./LibraryList";
import styles from "./LibraryManagement.module.scss";
import { PathInputWithSuggestions } from "./PathInputWithSuggestions";

/**
 * Library management component.
 *
 * Provides UI for managing libraries (add, toggle, delete).
 * Follows SRP by delegating business logic to hooks.
 * Uses IOC by accepting context dependencies.
 */
export function LibraryManagement() {
  const { refresh: refreshActiveLibrary } = useActiveLibrary();
  const [newPath, setNewPath] = useState("");
  const [newName, setNewName] = useState("");

  const {
    libraries,
    isLoading,
    isBusy,
    error,
    deletingLibraryId,
    addLibrary,
    toggleLibrary,
    deleteLibrary,
    clearError,
  } = useLibraryManagement({
    onRefresh: refreshActiveLibrary,
  });

  const handleAdd = useCallback(async () => {
    try {
      await addLibrary(newPath, newName);
      setNewPath("");
      setNewName("");
    } catch {
      // Error is handled by the hook
    }
  }, [newPath, newName, addLibrary]);

  const handlePathChange = useCallback(
    (value: string) => {
      setNewPath(value);
      clearError();
    },
    [clearError],
  );

  const handleNameChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setNewName(e.target.value);
      clearError();
    },
    [clearError],
  );

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
            onChange={handleNameChange}
            placeholder="Library name (optional)"
            className={styles.nameInput}
            disabled={isBusy}
          />
          <PathInputWithSuggestions
            value={newPath}
            onChange={handlePathChange}
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
        onToggle={toggleLibrary}
        onDelete={deleteLibrary}
        deletingLibraryId={deletingLibraryId}
      />
    </div>
  );
}
