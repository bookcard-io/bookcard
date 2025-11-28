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
import { OpenLibrarySettings } from "../openlibrary/OpenLibrarySettings";
import { IngestConfigSettings } from "../ingest/IngestConfigSettings";
import { useCollapsibleSection } from "@/hooks/useCollapsibleSection";
import { cn } from "@/libs/utils";

/**
 * Collapsible section wrapper component.
 */
function CollapsibleSection({
  title,
  description,
  isExpanded,
  onToggle,
  children,
}: {
  title: string;
  description: string;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full cursor-pointer items-center justify-between border-0 bg-transparent px-6 py-4 text-left transition-colors hover:bg-surface-a10"
      >
        <div className="flex flex-col gap-1">
          <h2 className="font-semibold text-text-a0 text-xl">{title}</h2>
          <p className="text-sm text-text-a30 leading-relaxed">{description}</p>
        </div>
        <i
          className={cn(
            "pi shrink-0 text-lg text-text-a30 transition-transform duration-200",
            isExpanded ? "pi-chevron-up" : "pi-chevron-down",
          )}
          aria-hidden="true"
        />
      </button>
      {isExpanded && (
        <div className="border-t border-surface-a20 px-6 py-4">
          {children}
        </div>
      )}
    </div>
  );
}

export function ConfigurationTab() {
  const ingestSection = useCollapsibleSection({ initialExpanded: true });
  const openLibrarySection = useCollapsibleSection({ initialExpanded: false });

  return (
    <div className="flex flex-col gap-6">
      <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-6">
        <h2 className="mb-4 font-semibold text-text-a0 text-xl">
          Library Management
        </h2>
        <p className="mb-4 text-sm text-text-a30 leading-relaxed">
          Manage multiple Calibre libraries. Only one library can be active at a
          time. The active library is used for all book operations.
        </p>
        <LibraryManagement />
      </div>

      <CollapsibleSection
        title="Ingestion Configuration"
        description="Configure automatic book ingestion settings including watch directory, metadata providers, retry settings, and processing options."
        isExpanded={ingestSection.isExpanded}
        onToggle={ingestSection.toggle}
      >
        <IngestConfigSettings />
      </CollapsibleSection>

      <CollapsibleSection
        title="OpenLibrary Data Dumps"
        description="OpenLibrary data dumps are automatically downloaded for library scans, provided for free by OpenLibrary. You can trigger a manual download here to fetch the latest data."
        isExpanded={openLibrarySection.isExpanded}
        onToggle={openLibrarySection.toggle}
      >
        <OpenLibrarySettings />
      </CollapsibleSection>
    </div>
  );
}
