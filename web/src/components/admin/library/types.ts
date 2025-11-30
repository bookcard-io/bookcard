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
  auto_convert_on_ingest: boolean;
  auto_convert_target_format: string | null;
  auto_convert_ignored_formats: string | null;
  auto_convert_backup_originals: boolean;
  epub_fixer_auto_fix_on_ingest: boolean;
  duplicate_handling: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
