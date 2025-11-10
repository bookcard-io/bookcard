"use client";

import { MainContent } from "@/components/library/MainContent";
import { Sidebar } from "@/components/sidebar/Sidebar";
import { ActiveLibraryProvider } from "@/contexts/ActiveLibraryContext";
import { SelectedBooksProvider } from "@/contexts/SelectedBooksContext";
import { SidebarProvider } from "@/contexts/SidebarContext";

export default function Home() {
  return (
    <ActiveLibraryProvider>
      <SelectedBooksProvider>
        <SidebarProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <MainContent />
          </div>
        </SidebarProvider>
      </SelectedBooksProvider>
    </ActiveLibraryProvider>
  );
}
