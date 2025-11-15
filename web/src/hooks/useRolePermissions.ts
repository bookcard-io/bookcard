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

import { useEffect, useMemo, useState } from "react";
import { fetchPermissions, type Permission } from "@/services/roleService";
import { validateConditionJson } from "@/utils/permissionValidation";

export interface NewPermissionDetails {
  description: string;
  resource: string;
  action: string;
  condition: string;
}

export interface UseRolePermissionsOptions {
  /** Initial permission names. */
  initialPermissionNames?: string[];
  /** All available permissions for reference. */
  availablePermissions?: Permission[];
}

export interface UseRolePermissionsReturn {
  /** Current permission names. */
  permissionNames: string[];
  /** Map of new permission details. */
  newPermissionDetails: Record<string, NewPermissionDetails>;
  /** Map of condition validation errors. */
  conditionErrors: Record<string, string>;
  /** All available permissions (provided or fetched). */
  allPermissions: Permission[];
  /** Map of permission names to Permission objects. */
  permissionMap: Map<string, Permission>;
  /** Existing permission names (found in permissionMap). */
  existingPermissionNames: string[];
  /** New permission names (not found in permissionMap). */
  newPermissionNames: string[];
  /** Whether permissions are being loaded. */
  isLoadingPermissions: boolean;
  /** Update permission names. */
  setPermissionNames: (names: string[]) => void;
  /** Remove an existing permission. */
  removeExistingPermission: (permissionName: string) => void;
  /** Remove a new permission. */
  removeNewPermission: (permissionName: string) => void;
  /** Update new permission details. */
  updateNewPermissionDetail: (
    permissionName: string,
    field: keyof NewPermissionDetails,
    value: string,
  ) => void;
  /** Reset to initial state. */
  reset: () => void;
}

/**
 * Hook for managing role permissions state.
 *
 * Handles permission names, new permission details, condition validation,
 * and permission fetching. Follows SRP by focusing solely on permission management.
 * Follows DRY by centralizing permission state logic.
 * Follows IOC by accepting initial state and callbacks.
 *
 * Parameters
 * ----------
 * options : UseRolePermissionsOptions
 *     Configuration options for the hook.
 *
 * Returns
 * -------
 * UseRolePermissionsReturn
 *     Object with permission state and handlers.
 */
export function useRolePermissions(
  options: UseRolePermissionsOptions = {},
): UseRolePermissionsReturn {
  const { initialPermissionNames = [], availablePermissions = [] } = options;

  const [permissionNames, setPermissionNames] = useState<string[]>(
    initialPermissionNames,
  );
  const [newPermissionDetails, setNewPermissionDetails] = useState<
    Record<string, NewPermissionDetails>
  >({});
  const [conditionErrors, setConditionErrors] = useState<
    Record<string, string>
  >({});

  // Fetch permissions if not provided
  const [fetchedPermissions, setFetchedPermissions] = useState<Permission[]>(
    [],
  );
  const [isLoadingPermissions, setIsLoadingPermissions] = useState(false);

  useEffect(() => {
    if (availablePermissions.length > 0) {
      return; // Use provided permissions
    }

    const loadPermissions = async () => {
      setIsLoadingPermissions(true);
      try {
        const permissions = await fetchPermissions();
        setFetchedPermissions(permissions);
      } catch (err) {
        console.error("Failed to fetch permissions:", err);
        // Silently fail - suggestions will still work via the hook
      } finally {
        setIsLoadingPermissions(false);
      }
    };

    void loadPermissions();
  }, [availablePermissions.length]);

  // Use provided permissions or fetched permissions
  const allPermissions = useMemo(() => {
    return availablePermissions.length > 0
      ? availablePermissions
      : fetchedPermissions;
  }, [availablePermissions, fetchedPermissions]);

  // Create a map of permission names to Permission objects for quick lookup
  const permissionMap = useMemo(() => {
    const map = new Map<string, Permission>();
    allPermissions.forEach((perm) => {
      map.set(perm.name, perm);
    });
    return map;
  }, [allPermissions]);

  // Separate existing and new permissions
  const existingPermissionNames = useMemo(() => {
    return permissionNames.filter((name) => permissionMap.has(name));
  }, [permissionNames, permissionMap]);

  const newPermissionNames = useMemo(() => {
    return permissionNames.filter((name) => !permissionMap.has(name));
  }, [permissionNames, permissionMap]);

  const removeExistingPermission = (permissionName: string) => {
    setPermissionNames((prev) =>
      prev.filter((name) => name !== permissionName),
    );
  };

  const removeNewPermission = (permissionName: string) => {
    setPermissionNames((prev) =>
      prev.filter((name) => name !== permissionName),
    );
    setNewPermissionDetails((prev) => {
      const updated = { ...prev };
      delete updated[permissionName];
      return updated;
    });
    setConditionErrors((prev) => {
      const updated = { ...prev };
      delete updated[permissionName];
      return updated;
    });
  };

  const updateNewPermissionDetail = (
    permissionName: string,
    field: keyof NewPermissionDetails,
    value: string,
  ) => {
    setNewPermissionDetails((prev) => {
      const current = prev[permissionName] || {
        description: "",
        resource: "",
        action: "",
        condition: "",
      };
      return {
        ...prev,
        [permissionName]: {
          ...current,
          [field]: value,
        },
      };
    });

    // Validate condition JSON if it's the condition field
    if (field === "condition") {
      const error = validateConditionJson(value);
      setConditionErrors((prev) => ({
        ...prev,
        [permissionName]: error || "",
      }));
    }
  };

  const reset = () => {
    setPermissionNames(initialPermissionNames);
    setNewPermissionDetails({});
    setConditionErrors({});
  };

  return {
    permissionNames,
    newPermissionDetails,
    conditionErrors,
    allPermissions,
    permissionMap,
    existingPermissionNames,
    newPermissionNames,
    isLoadingPermissions,
    setPermissionNames,
    removeExistingPermission,
    removeNewPermission,
    updateNewPermissionDetail,
    reset,
  };
}
