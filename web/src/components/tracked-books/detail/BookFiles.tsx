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

import { FaDownload, FaFile, FaTrash } from "react-icons/fa";
import type { BookFile } from "@/types/trackedBook";
import { byteFormatter } from "@/utils/formatters";

interface BookFilesProps {
  files?: BookFile[];
}

export function BookFiles({ files }: BookFilesProps) {
  return (
    <div className="flex flex-col gap-4 border-surface-a20 bg-surface-a0 p-6 md:px-8">
      <h2 className="border-surface-a20 border-b pb-2 font-bold text-text-a0 text-xl">
        Files
      </h2>
      <div className="overflow-hidden rounded-md border border-surface-a20 bg-surface-a0">
        {/* Header */}
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 bg-surface-tonal-a10 px-4 py-3 font-bold text-text-a30 text-xs uppercase tracking-wider md:grid-cols-[1fr_100px_100px_100px_80px]">
          <div className="flex items-center gap-1">Relative Path</div>
          <div className="text-right">Format</div>
          <div className="text-right">Size</div>
          <div className="text-right">Language</div>
          <div className="text-center">Actions</div>
        </div>

        {/* File List or Empty State */}
        {!files || files.length === 0 ? (
          <div className="flex items-center justify-center bg-surface-a10/50 p-8 text-sm text-text-a30">
            No files to manage.
          </div>
        ) : (
          <div className="divide-y divide-surface-a10">
            {files.map((file, idx) => (
              <div
                // biome-ignore lint/suspicious/noArrayIndexKey: Files don't have unique IDs yet
                key={idx}
                className="grid grid-cols-[1fr_auto_auto_auto_auto] items-center gap-4 px-4 py-3 text-sm transition-colors hover:bg-surface-a10/30 md:grid-cols-[1fr_100px_100px_100px_80px]"
              >
                <div className="flex items-center gap-3 overflow-hidden">
                  <FaFile className="text-text-a30" />
                  <span className="truncate" title={file.name}>
                    {file.name}
                  </span>
                </div>
                <div className="text-right font-medium text-text-a30 uppercase">
                  {file.format}
                </div>
                <div className="text-right text-text-a30">
                  {byteFormatter.format(file.size)}
                </div>
                <div className="text-right text-text-a30">-</div>
                <div className="flex justify-center gap-2">
                  <button
                    type="button"
                    className="p-1.5 text-text-a30 transition-colors hover:text-primary-a0"
                    title="Download"
                    onClick={() => {
                      // TODO: Implement download
                      console.log("Download", file.path);
                    }}
                  >
                    <FaDownload size={14} />
                  </button>
                  <button
                    type="button"
                    className="p-1.5 text-text-a30 transition-colors hover:text-danger-a0"
                    title="Delete"
                    onClick={() => {
                      // TODO: Implement delete
                      console.log("Delete", file.path);
                    }}
                  >
                    <FaTrash size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
