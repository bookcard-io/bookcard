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

import Link from "next/link";
import { Suspense } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { MainContent } from "@/components/library/MainContent";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { useUser } from "@/contexts/UserContext";
import { useAnonymousAccessConfig } from "@/hooks/useAnonymousAccessConfig";

function GatedHome() {
  const { user, isLoading: isUserLoading } = useUser();
  const {
    config,
    isLoading: isConfigLoading,
    error,
  } = useAnonymousAccessConfig();

  const allowAnonymous = config?.allow_anonymous_browsing ?? false;
  const isLoading = isUserLoading || isConfigLoading;

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-text-a40">
        Loading...
      </div>
    );
  }

  if ((!allowAnonymous || error) && !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-surface-a0">
        <div className="rounded-md border border-surface-a20 bg-surface-tonal-a0 p-8 shadow-sm">
          <h1 className="mb-3 text-center font-semibold text-text-a0 text-xl">
            Sign in to view the library
          </h1>
          <p className="mb-6 text-center text-text-a30">
            Anonymous browsing is disabled. Please log in to continue.
          </p>
          <div className="flex justify-center">
            <Link
              href="/login?next=%2F"
              prefetch={false}
              className="rounded-md bg-primary-a0 px-4 py-2 font-medium text-[var(--color-text-primary-a0)] text-sm transition-colors hover:bg-[var(--clr-primary-a10)]"
            >
              Go to login
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <MainContent />;
}

export default function Home() {
  return (
    <SelectedBooksProvider>
      <PageLayout>
        <Suspense fallback={<div className="p-6">Loading library...</div>}>
          <GatedHome />
        </Suspense>
      </PageLayout>
    </SelectedBooksProvider>
  );
}
