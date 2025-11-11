"use client";

import { AdminSettings } from "@/components/admin/AdminSettings";
import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";

/**
 * Admin settings page.
 *
 * Uses PageLayout for consistent sidebar and context provider setup.
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 */
export default function AdminPage() {
  return (
    <PageLayout>
      <PageHeader title="Admin Settings" />
      <AdminSettings />
    </PageLayout>
  );
}
