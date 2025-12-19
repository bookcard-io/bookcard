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
import { Suspense, useEffect } from "react";
import { PageLayout } from "@/components/layout/PageLayout";
import { MainContent } from "@/components/library/MainContent";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { useUser } from "@/contexts/UserContext";
import { useAnonymousAccessConfig } from "@/hooks/useAnonymousAccessConfig";

function GatedHome() {
  const router = useRouter();
  const { user, isLoading: isUserLoading } = useUser();
  const {
    config,
    isLoading: isConfigLoading,
    error,
  } = useAnonymousAccessConfig();

  const allowAnonymous = config?.allow_anonymous_browsing ?? false;
  const isLoading = isUserLoading || isConfigLoading;

  useEffect(() => {
    if (!isLoading && (!allowAnonymous || error) && !user) {
      router.replace("/login?next=%2F");
    }
  }, [isLoading, allowAnonymous, error, user, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-text-a40">
        Loading...
      </div>
    );
  }

  if ((!allowAnonymous || error) && !user) {
    return null;
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
