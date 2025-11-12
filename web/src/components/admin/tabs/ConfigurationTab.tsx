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

import { LibraryManagement } from "../library/LibraryManagement";

export function ConfigurationTab() {
  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-lg border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          Library Management
        </h2>
        <p className="mb-4 text-sm text-text-a30 leading-relaxed">
          Manage multiple Calibre libraries. Only one library can be active at a
          time. The active library is used for all book operations.
        </p>
        <LibraryManagement />
      </div>

      <div className="rounded-lg border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          Email Server Settings
        </h2>
        <p className="text-sm text-text-a30">
          Email server configuration will be implemented here.
        </p>
      </div>

      <div className="rounded-lg border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          Basic Configuration
        </h2>
        <p className="text-sm text-text-a30">
          Basic system configuration will be implemented here.
        </p>
      </div>

      <div className="rounded-lg border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          UI Configuration
        </h2>
        <p className="text-sm text-text-a30">
          UI settings and preferences will be implemented here.
        </p>
      </div>
    </div>
  );
}
