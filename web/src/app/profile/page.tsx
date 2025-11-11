"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { ProfileSettings } from "@/components/profile/ProfileSettings";

/**
 * User profile and settings page.
 *
 * Uses PageLayout for consistent sidebar and context provider setup.
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 */
export default function ProfilePage() {
  return (
    <PageLayout>
      <PageHeader title="Profile" />
      <ProfileSettings />
    </PageLayout>
  );
}
