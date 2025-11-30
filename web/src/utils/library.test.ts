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

import { describe, expect, it } from "vitest";
import type { Library } from "@/components/admin/library/types";
import { generateLibraryName } from "./library";

describe("library utils", () => {
  describe("generateLibraryName", () => {
    it("should return provided name when trimmed name is provided", () => {
      const existingLibraries: Library[] = [];
      const result = generateLibraryName(
        existingLibraries,
        "My Custom Library",
      );
      expect(result).toBe("My Custom Library");
    });

    it("should return trimmed provided name", () => {
      const existingLibraries: Library[] = [];
      const result = generateLibraryName(
        existingLibraries,
        "  Trimmed Library  ",
      );
      expect(result).toBe("Trimmed Library");
    });

    it("should return 'My Library' when no libraries exist and no name provided", () => {
      const existingLibraries: Library[] = [];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library");
    });

    it("should return 'My Library (1)' when 'My Library' exists", () => {
      const existingLibraries: Library[] = [
        {
          id: 1,
          name: "My Library",
          calibre_db_path: "",
          calibre_db_file: "",
          calibre_uuid: null,
          use_split_library: false,
          split_library_dir: null,
          auto_reconnect: false,
          auto_convert_on_ingest: false,
          auto_convert_target_format: null,
          auto_convert_ignored_formats: null,
          auto_convert_backup_originals: true,
          is_active: false,
          created_at: "",
          updated_at: "",
        },
      ];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library (1)");
    });

    it("should return 'My Library (2)' when 'My Library' and 'My Library (1)' exist", () => {
      const existingLibraries: Library[] = [
        {
          id: 1,
          name: "My Library",
          calibre_db_path: "",
          calibre_db_file: "",
          calibre_uuid: null,
          use_split_library: false,
          split_library_dir: null,
          auto_reconnect: false,
          auto_convert_on_ingest: false,
          auto_convert_target_format: null,
          auto_convert_ignored_formats: null,
          auto_convert_backup_originals: true,
          is_active: false,
          created_at: "",
          updated_at: "",
        },
        {
          id: 2,
          name: "My Library (1)",
          calibre_db_path: "",
          calibre_db_file: "",
          calibre_uuid: null,
          use_split_library: false,
          split_library_dir: null,
          auto_reconnect: false,
          auto_convert_on_ingest: false,
          auto_convert_target_format: null,
          auto_convert_ignored_formats: null,
          auto_convert_backup_originals: true,
          is_active: false,
          created_at: "",
          updated_at: "",
        },
      ];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library (2)");
    });

    it("should return 'My Library (3)' when numbered libraries exist with gaps", () => {
      const createLibrary = (id: number, name: string): Library => ({
        id,
        name,
        calibre_db_path: "",
        calibre_db_file: "",
        calibre_uuid: null,
        use_split_library: false,
        split_library_dir: null,
        auto_reconnect: false,
        auto_convert_on_ingest: false,
        auto_convert_target_format: null,
        auto_convert_ignored_formats: null,
        auto_convert_backup_originals: true,
        is_active: false,
        created_at: "",
        updated_at: "",
      });
      const existingLibraries: Library[] = [
        createLibrary(1, "My Library"),
        createLibrary(2, "My Library (1)"),
        createLibrary(3, "My Library (3)"),
      ];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library (4)");
    });

    it("should return 'My Library (1)' when only numbered libraries exist without base name", () => {
      const createLibrary = (id: number, name: string): Library => ({
        id,
        name,
        calibre_db_path: "",
        calibre_db_file: "",
        calibre_uuid: null,
        use_split_library: false,
        split_library_dir: null,
        auto_reconnect: false,
        auto_convert_on_ingest: false,
        auto_convert_target_format: null,
        auto_convert_ignored_formats: null,
        auto_convert_backup_originals: true,
        is_active: false,
        created_at: "",
        updated_at: "",
      });
      const existingLibraries: Library[] = [
        createLibrary(1, "My Library (2)"),
        createLibrary(2, "My Library (5)"),
      ];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library (6)");
    });

    it("should ignore libraries that don't match the pattern", () => {
      const createLibrary = (id: number, name: string): Library => ({
        id,
        name,
        calibre_db_path: "",
        calibre_db_file: "",
        calibre_uuid: null,
        use_split_library: false,
        split_library_dir: null,
        auto_reconnect: false,
        auto_convert_on_ingest: false,
        auto_convert_target_format: null,
        auto_convert_ignored_formats: null,
        auto_convert_backup_originals: true,
        is_active: false,
        created_at: "",
        updated_at: "",
      });
      const existingLibraries: Library[] = [
        createLibrary(1, "Other Library"),
        createLibrary(2, "My Library (1)"),
      ];
      const result = generateLibraryName(existingLibraries);
      expect(result).toBe("My Library (2)");
    });

    it("should return provided name even if it matches pattern", () => {
      const existingLibraries: Library[] = [
        {
          id: 1,
          name: "My Library",
          calibre_db_path: "",
          calibre_db_file: "",
          calibre_uuid: null,
          use_split_library: false,
          split_library_dir: null,
          auto_reconnect: false,
          auto_convert_on_ingest: false,
          auto_convert_target_format: null,
          auto_convert_ignored_formats: null,
          auto_convert_backup_originals: true,
          is_active: false,
          created_at: "",
          updated_at: "",
        },
      ];
      const result = generateLibraryName(existingLibraries, "My Library (1)");
      expect(result).toBe("My Library (1)");
    });

    it("should return 'My Library' when provided name is only whitespace", () => {
      const existingLibraries: Library[] = [];
      const result = generateLibraryName(existingLibraries, "   ");
      expect(result).toBe("My Library");
    });
  });
});
