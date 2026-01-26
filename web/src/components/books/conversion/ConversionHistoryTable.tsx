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

import type { BookConversionListResponse } from "@/services/bookService";
import { StatusBadge } from "./StatusBadge";

export interface ConversionHistoryTableProps {
  /** Conversion history response. */
  history: BookConversionListResponse | undefined;
}

export function ConversionHistoryTable({
  history,
}: ConversionHistoryTableProps) {
  if (!history?.items?.length) {
    return null;
  }

  return (
    <div className="mb-6">
      <h3 className="mb-2 font-semibold text-[var(--color-text-a0)] text-sm">
        Conversion History
      </h3>
      <div className="max-h-[200px] overflow-y-auto rounded-md border border-[var(--color-surface-a20)]">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-[var(--color-surface-a10)]">
            <tr>
              <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                From
              </th>
              <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                To
              </th>
              <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                Status
              </th>
              <th className="px-3 py-2 text-left text-[var(--color-text-a20)]">
                Date
              </th>
            </tr>
          </thead>
          <tbody>
            {history.items.map((conv) => (
              <tr
                key={conv.id}
                className="border-[var(--color-surface-a20)] border-t"
              >
                <td className="px-3 py-2 text-[var(--color-text-a0)]">
                  {conv.original_format}
                </td>
                <td className="px-3 py-2 text-[var(--color-text-a0)]">
                  {conv.target_format}
                </td>
                <td className="px-3 py-2">
                  <StatusBadge status={conv.status} />
                </td>
                <td className="px-3 py-2 text-[var(--color-text-a20)] text-xs">
                  {new Date(conv.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
