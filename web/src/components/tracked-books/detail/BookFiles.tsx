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

export function BookFiles() {
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

        {/* Empty State */}
        <div className="flex items-center justify-center bg-surface-a10/50 p-8 text-sm text-text-a30">
          No files to manage.
        </div>
      </div>
    </div>
  );
}
