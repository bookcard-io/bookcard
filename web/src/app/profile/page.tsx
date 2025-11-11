"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { useUserProfile } from "@/components/profile/hooks/useUserProfile";
import { ProfileSettings } from "@/components/profile/ProfileSettings";

/**
 * User profile and settings page.
 *
 * Uses PageLayout for consistent sidebar and context provider setup.
 * Standard action bar buttons (Profile, Admin) are automatically included
 * via the HeaderActionBarButtons component in PageLayout.
 */
export default function ProfilePage() {
  const { user } = useUserProfile();

  const greeting = user
    ? `Hello ${user.full_name ?? user.username}`
    : "Profile";

  return (
    <PageLayout>
      <PageHeader title={greeting} />
      <ProfileSettings />
    </PageLayout>
  );
}
