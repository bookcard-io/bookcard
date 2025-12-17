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

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useUser } from "@/contexts/UserContext";

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

interface ActiveLibraryContextType {
  activeLibrary: Library | null;
  isLoading: boolean;
  refresh: () => Promise<void>;
}

const ActiveLibraryContext = createContext<
  ActiveLibraryContextType | undefined
>(undefined);

export function ActiveLibraryProvider({ children }: { children: ReactNode }) {
  const { isLoading: userLoading } = useUser();
  const [activeLibrary, setActiveLibrary] = useState<Library | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    // Wait for user to load before fetching
    if (userLoading) {
      return;
    }

    // Active library is readable by:
    // - authenticated users
    // - anonymous users when anonymous browsing is enabled
    try {
      setIsLoading(true);
      const response = await fetch("/api/libraries/active");
      if (response.ok) {
        const data = await response.json();
        setActiveLibrary(data);
      } else {
        setActiveLibrary(null);
      }
    } catch {
      setActiveLibrary(null);
    } finally {
      setIsLoading(false);
    }
  }, [userLoading]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <ActiveLibraryContext.Provider
      value={{ activeLibrary, isLoading, refresh }}
    >
      {children}
    </ActiveLibraryContext.Provider>
  );
}

export function useActiveLibrary() {
  const context = useContext(ActiveLibraryContext);
  if (context === undefined) {
    throw new Error(
      "useActiveLibrary must be used within an ActiveLibraryProvider",
    );
  }
  return context;
}
