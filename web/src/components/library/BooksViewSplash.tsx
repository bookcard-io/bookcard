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

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import {
  FaBookReader,
  FaDatabase,
  FaMobileAlt,
  FaShieldAlt,
  FaSync,
} from "react-icons/fa";
import { GiBookshelf } from "react-icons/gi";
import { useLibraryManagement } from "@/components/admin/library/hooks/useLibraryManagement";
import { Button } from "@/components/forms/Button";
import { useActiveLibrary } from "@/contexts/ActiveLibraryContext";

/**
 * Splash screen component for when no library is active.
 *
 * Introduces users to Bookcard with feature highlights and
 * provides options to use existing library or create a new one.
 * Follows SRP by handling only the splash screen display and actions.
 */
export function BooksViewSplash() {
  const router = useRouter();
  const { refresh: refreshActiveLibrary } = useActiveLibrary();
  const [isCreating, setIsCreating] = useState(false);

  const { createLibrary, isBusy } = useLibraryManagement({
    onRefresh: refreshActiveLibrary,
  });

  const handleUseExistingLibrary = useCallback(() => {
    router.push("/admin?tab=configuration");
  }, [router]);

  const handleCreateLibrary = useCallback(async () => {
    try {
      setIsCreating(true);
      await createLibrary("My Library");
    } catch {
      // Error is handled by the hook
    } finally {
      setIsCreating(false);
    }
  }, [createLibrary]);

  const features = [
    {
      icon: FaBookReader,
      title: "Web-based Reading",
      description:
        "Read ebooks directly in your browser with customizable themes",
    },
    {
      icon: GiBookshelf,
      title: "Library Management",
      description:
        "Organize books into shelves, search and filter your collection",
    },
    {
      icon: FaDatabase,
      title: "Metadata Enrichment",
      description:
        "Automatic fetching from multiple providers (Google Books, Open Library, etc.)",
    },
    {
      icon: FaSync,
      title: "Library Scanning",
      description:
        "Background process linking your library to authoritative databases",
    },
    {
      icon: FaMobileAlt,
      title: "Modern Interface",
      description: "Responsive design that works on desktop and mobile devices",
    },
    {
      icon: FaShieldAlt,
      title: "Self-hosted",
      description: "Full control over your data and privacy",
    },
  ];

  const leftColumnFeatures = features.slice(0, 3);
  const rightColumnFeatures = features.slice(3);

  return (
    <div className="flex min-h-[calc(100vh-200px)] items-center justify-center p-8">
      <div className="mx-auto w-full max-w-4xl">
        <div className="mb-8 text-center">
          <h1 className="mb-3 font-bold text-3xl text-text-a0">
            Welcome to Bookcard
          </h1>
          <p className="text-base text-text-a30">
            A modern, self-hosted ebook management and reading platform
          </p>
        </div>

        <div className="mb-8 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="flex flex-col gap-4">
            {leftColumnFeatures.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="flex items-start gap-3">
                  <div className="mt-1 flex-shrink-0">
                    <Icon className="h-5 w-5 text-primary-a0" />
                  </div>
                  <div>
                    <h3 className="mb-1 font-semibold text-sm text-text-a0">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-text-a30">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex flex-col gap-4">
            {rightColumnFeatures.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="flex items-start gap-3">
                  <div className="mt-1 flex-shrink-0">
                    <Icon className="h-5 w-5 text-primary-a0" />
                  </div>
                  <div>
                    <h3 className="mb-1 font-semibold text-sm text-text-a0">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-text-a30">
                      {feature.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="flex flex-col items-center gap-8 sm:flex-row sm:justify-center">
          <Button
            variant="primary"
            size="medium"
            onClick={handleUseExistingLibrary}
            disabled={isBusy || isCreating}
          >
            Use existing library
          </Button>

          <div className="flex items-center">
            <div className="hidden h-8 w-px bg-[var(--color-surface-a20)] sm:block" />
            <div className="block h-px w-8 bg-[var(--color-surface-a20)] sm:hidden" />
          </div>

          <Button
            variant="success"
            size="medium"
            onClick={handleCreateLibrary}
            disabled={isBusy || isCreating}
            loading={isCreating}
          >
            Create new library
          </Button>
        </div>

        <p className="mt-4 text-center text-text-a30 text-xs">
          Connect an existing Calibre{" "}
          <code className="rounded bg-surface-a10 px-1 py-0.5 text-xs">
            metadata.db
          </code>{" "}
          or create a fresh library
        </p>
      </div>
    </div>
  );
}
