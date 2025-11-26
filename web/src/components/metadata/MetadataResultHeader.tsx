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

import { ImageWithLoading } from "@/components/common/ImageWithLoading";
import type { MetadataRecord } from "@/hooks/useMetadataSearchStream";

export interface MetadataResultHeaderProps {
  record: MetadataRecord;
  isExpanded: boolean;
  onClick: () => void;
}

/**
 * Header component for metadata result item.
 *
 * Displays title, author, publisher, and source link.
 * Follows SRP by focusing solely on header presentation.
 * Follows IOC by accepting callbacks as props.
 *
 * Parameters
 * ----------
 * props : MetadataResultHeaderProps
 *     Component props including record, expanded state, and click handler.
 */
export function MetadataResultHeader({
  record,
  isExpanded,
  onClick,
}: MetadataResultHeaderProps) {
  if (isExpanded) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex w-full cursor-pointer gap-3 rounded border-0 bg-transparent p-0 text-left transition-opacity hover:opacity-80"
        aria-label={`Collapse fields selection for ${record.title}`}
      >
        <div className="flex min-w-0 flex-1 flex-col gap-[0.35rem]">
          <div className="flex items-baseline gap-2">
            <div className="min-w-0 flex-1 font-bold text-lg text-text-a0 leading-[1.3]">
              {record.title}
            </div>
            {record.publisher && (
              <div className="whitespace-nowrap text-sm text-text-a30">
                {record.publisher}
              </div>
            )}
          </div>
          {record.authors && record.authors.length > 0 && (
            <div className="flex gap-2 text-sm">
              <span className="text-text-a30">Author</span>
              <span className="text-text-a0">{record.authors.join(", ")}</span>
            </div>
          )}
          <div className="mt-1">
            <a
              href={record.url}
              className="text-primary-a0 no-underline hover:underline"
              target="_blank"
              rel="noreferrer"
              onClick={(e) => e.stopPropagation()}
            >
              Source: {record.source_id}
            </a>
          </div>
        </div>
      </button>
    );
  }

  return (
    <div className="flex gap-3">
      <div className="shrink-0">
        {record.cover_url ? (
          <button
            type="button"
            onClick={onClick}
            className="cursor-pointer border-0 bg-transparent p-0 transition-[transform,box-shadow] duration-200 ease-in-out hover:scale-105 active:scale-[0.98]"
            aria-label={`Select fields to import from ${record.title}`}
            title="Click to select fields to import"
          >
            <ImageWithLoading
              src={record.cover_url}
              alt={`Cover for ${record.title}`}
              width={60}
              height={90}
              className="block rounded border object-cover shadow-[0_2px_8px_rgba(0,0,0,0.3)]"
              unoptimized
            />
          </button>
        ) : (
          <div
            className="h-[90px] w-[60px] rounded border bg-surface-a20"
            aria-hidden="true"
          />
        )}
      </div>
      <div className="flex min-w-0 flex-1 flex-col gap-[0.35rem]">
        <div className="flex items-baseline gap-2">
          <div className="min-w-0 flex-1 font-semibold text-[0.95rem] text-text-a0 leading-[1.3]">
            {record.title}
          </div>
          {record.publisher && (
            <div className="whitespace-nowrap text-text-a30 text-xs">
              {record.publisher}
            </div>
          )}
        </div>
        {record.authors && record.authors.length > 0 && (
          <div className="flex gap-2 text-[0.8rem]">
            <span className="text-text-a30">Author</span>
            <span className="text-text-a0">{record.authors.join(", ")}</span>
          </div>
        )}
        {record.description && (
          <div
            className="line-clamp-3 text-[0.85rem] text-text-a20 leading-[1.4]"
            title={record.description}
          >
            {record.description}
          </div>
        )}
        <div className="mt-1">
          <a
            href={record.url}
            className="text-primary-a0 no-underline hover:underline"
            target="_blank"
            rel="noreferrer"
          >
            Source: {record.source_id}
          </a>
        </div>
      </div>
    </div>
  );
}
