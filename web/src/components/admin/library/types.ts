/**
 * Shared types for library components.
 *
 * Centralizes type definitions to avoid duplication (DRY).
 */

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
