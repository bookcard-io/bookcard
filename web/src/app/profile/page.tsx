"use client";

import { PageLayout } from "@/components/layout/PageLayout";
import { ProfileSettings } from "@/components/profile/ProfileSettings";

/**
 * User profile and settings page.
 *
 * Uses PageLayout for consistent sidebar and context provider setup.
 */
export default function ProfilePage() {
  return (
    <PageLayout>
      <ProfileSettings />
    </PageLayout>
  );
}
