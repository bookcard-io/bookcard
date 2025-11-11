"use client";

import { PageHeader } from "@/components/layout/PageHeader";
import { PageLayout } from "@/components/layout/PageLayout";
import { ProfileSettings } from "@/components/profile/ProfileSettings";
import { useUser } from "@/contexts/UserContext";

/**
 * Profile page content component.
 *
 * Rendered inside PageLayout so it has access to UserContext.
 */
function ProfilePageContent() {
  const { user } = useUser();

  const greeting = user
    ? `Hello ${user.full_name ?? user.username}`
    : "Profile";

  return (
    <>
      <PageHeader title={greeting} />
      <ProfileSettings />
    </>
  );
}

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
      <ProfilePageContent />
    </PageLayout>
  );
}
