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

import {
  FaCloudDownloadAlt,
  FaExclamationTriangle,
  FaSort,
  FaSortDown,
  FaSortUp,
  FaSpinner,
} from "react-icons/fa";
import { Button } from "@/components/forms/Button";
import type { SortDirection } from "@/hooks/pvr/useTableSort";
import { languageDetector } from "@/services/languageDetectionService";
import type { SearchResultRead } from "@/types/pvrSearch";
import { byteFormatter, dateFormatter } from "@/utils/formatters";

interface SearchResultsTableProps {
  results: SearchResultRead[];
  sortConfig: { key: string; direction: SortDirection } | null;
  onSort: (key: string) => void;
  onDownload: (index: number) => void;
  downloadingIndex: number | null;
}

export function SearchResultsTable({
  results,
  sortConfig,
  onSort,
  onDownload,
  downloadingIndex,
}: SearchResultsTableProps) {
  const getSortIcon = (key: string) => {
    if (sortConfig?.key !== key)
      return <FaSort className="ml-1 inline opacity-20" />;
    return sortConfig.direction === "asc" ? (
      <FaSortUp className="ml-1 inline text-primary-a10" />
    ) : (
      <FaSortDown className="ml-1 inline text-primary-a10" />
    );
  };

  return (
    <div className="overflow-hidden rounded-md border border-surface-a20 bg-surface-a0">
      <div className="grid grid-cols-[80px_100px_1fr_120px_100px_80px_100px_100px_60px] gap-4 border-surface-a20 border-b bg-surface-a10 px-4 py-3 font-bold text-text-a30 text-xs uppercase tracking-wider">
        <div>Source</div>
        <button
          type="button"
          className="w-full cursor-pointer select-none border-none bg-transparent p-0 text-left uppercase hover:text-text-a10"
          onClick={() => onSort("age")}
        >
          Age {getSortIcon("age")}
        </button>
        <button
          type="button"
          className="w-full cursor-pointer select-none border-none bg-transparent p-0 text-left uppercase hover:text-text-a10"
          onClick={() => onSort("title")}
        >
          Title {getSortIcon("title")}
        </button>
        <button
          type="button"
          className="w-full cursor-pointer select-none border-none bg-transparent p-0 text-left uppercase hover:text-text-a10"
          onClick={() => onSort("indexer")}
        >
          Indexer {getSortIcon("indexer")}
        </button>
        <button
          type="button"
          className="w-full cursor-pointer select-none border-none bg-transparent p-0 text-right uppercase hover:text-text-a10"
          onClick={() => onSort("size")}
        >
          Size {getSortIcon("size")}
        </button>
        <button
          type="button"
          className="w-full cursor-pointer select-none border-none bg-transparent p-0 text-right uppercase hover:text-text-a10"
          onClick={() => onSort("peers")}
        >
          Peers {getSortIcon("peers")}
        </button>
        <div>Lang</div>
        <div>Quality</div>
        <div className="text-center">Act</div>
      </div>

      {results.length === 0 ? (
        <div className="p-8 text-center text-text-a30">No results found.</div>
      ) : (
        results.map((result, idx) => (
          <div
            key={`${result.indexer_name}-${result.release.title}-${idx}`}
            className="grid grid-cols-[80px_100px_1fr_120px_100px_80px_100px_100px_60px] items-center gap-4 border-surface-a20 border-b px-4 py-3 text-sm text-text-a10 last:border-0 hover:bg-surface-a20"
          >
            <div>
              <span className="rounded bg-success-a10 px-1.5 py-0.5 font-medium text-black text-xs">
                {result.indexer_protocol || "torrent"}
              </span>
            </div>
            <div className="text-text-a30">
              {result.release.publish_date
                ? dateFormatter.toAge(result.release.publish_date)
                : "-"}
            </div>
            <div
              className="break-words font-medium"
              title={result.release.title}
            >
              {result.release.warning && (
                <FaExclamationTriangle
                  className="mr-2 inline text-warning-a10"
                  title={result.release.warning}
                />
              )}
              {result.release.title}
            </div>
            <div className="truncate text-text-a30">
              {result.indexer_name || "-"}
            </div>
            <div className="text-right font-mono text-xs">
              {byteFormatter.format(result.release.size_bytes)}
            </div>
            <div className="text-right">
              <span className="text-success-a10">
                {result.release.seeders ?? 0}
              </span>
              <span className="text-text-a40"> / </span>
              <span className="text-danger-a10">
                {result.release.leechers ?? 0}
              </span>
            </div>
            <div className="text-text-a30">
              {(() => {
                const lang = languageDetector.detect(result.release.title);
                return (
                  <span title={lang?.englishName}>
                    {lang?.flag} {lang?.englishName}
                  </span>
                );
              })()}
            </div>
            <div>
              <span className="rounded border border-surface-a30 px-1.5 py-0.5 font-medium text-text-a30 text-xs">
                {result.release.quality || "Unknown"}
              </span>
            </div>
            <div className="flex justify-center">
              <Button
                size="xsmall"
                variant="neutral"
                onClick={() => onDownload(idx)}
                disabled={downloadingIndex === idx}
                title="Download"
              >
                {downloadingIndex === idx ? (
                  <FaSpinner className="animate-spin text-lg" />
                ) : (
                  <FaCloudDownloadAlt className="text-lg" />
                )}
              </Button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
