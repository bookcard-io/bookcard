import type { ReactNode } from "react";
import { HeaderActionBar } from "@/components/layout/HeaderActionBar";
import { SearchInput } from "@/components/library/widgets/SearchInput";

interface TrackedBooksHeaderProps {
  searchQuery?: string;
  onSearchChange?: (query: string) => void;
  children?: ReactNode;
}

export function TrackedBooksHeader({
  searchQuery,
  onSearchChange,
  children,
}: TrackedBooksHeaderProps) {
  return (
    <header className="grid grid-cols-[minmax(0,1fr)_auto] grid-rows-2 gap-x-4 gap-y-2 px-8 pt-6 pb-4 sm:flex sm:items-center sm:justify-between">
      <div className="col-span-1 row-span-2 m-0 w-full max-w-xl">
        <SearchInput
          placeholder="Search tracked books..."
          value={searchQuery}
          onChange={onSearchChange}
        />
      </div>
      <div className="col-start-2 row-span-2 row-start-1 flex flex-col items-end gap-2 sm:col-auto sm:row-auto sm:flex-row sm:items-center sm:gap-3">
        {children}
        <HeaderActionBar />
      </div>
    </header>
  );
}
