"use client";

import styles from "./LibraryList.module.scss";

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
    <div className={styles.container}>
      {libraries.map((lib) => (
        <div key={lib.id} className={styles.libraryItem}>
          <div className={styles.checkboxLabel}>
            <input
              type="checkbox"
              checked={lib.is_active}
              onChange={() => onToggle(lib)}
              className={styles.checkbox}
            />
            <div className={styles.libraryInfo}>
              <div
                className={`${styles.libraryName} ${
                  lib.is_active ? styles.active : ""
                }`}
              >
                {lib.name}
              </div>
              <div className={styles.libraryPath}>{lib.calibre_db_path}</div>
              {lib.updated_at && (
                <div className={styles.updatedAt}>
                  Last updated: {new Date(lib.updated_at).toLocaleString()}
                </div>
              )}
            </div>
          </div>
          <button
            type="button"
            onClick={() => onDelete(lib.id)}
            disabled={deletingLibraryId === lib.id}
            className={`${styles.deleteButton} ${
              deletingLibraryId === lib.id ? styles.deleting : ""
            }`}
          >
            Remove
          </button>
        </div>
      ))}
      {libraries.length === 0 && (
        <div className={styles.empty}>No libraries configured yet.</div>
      )}
      {libraries.length > 0 && !libraries.some((lib) => lib.is_active) && (
        <div className={styles.empty}>
          Please activate a library to begin using the app.
        </div>
      )}
    </div>
  );
}
