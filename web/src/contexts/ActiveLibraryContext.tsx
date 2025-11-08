"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

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
  const [activeLibrary, setActiveLibrary] = useState<Library | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch("/api/admin/libraries/active");
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
  }, []);

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
