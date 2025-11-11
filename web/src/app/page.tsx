"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { MainContent } from "@/components/library/MainContent";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";

export default function Home() {
  return (
    <SelectedBooksProvider>
      <PageLayout>
        <MainContent />
      </PageLayout>
    </SelectedBooksProvider>
  );
}
