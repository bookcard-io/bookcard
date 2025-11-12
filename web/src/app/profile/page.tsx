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
