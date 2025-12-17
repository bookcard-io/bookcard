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

import { defaultRouteConfig } from "./config";
import type { RouteClassification, RouteConfig } from "./types";

/**
 * Classifies a route based on configuration.
 *
 * Follows SRP by handling only route classification.
 * Follows OCP by using configuration-driven patterns.
 *
 * Parameters
 * ----------
 * pathname : string
 *     The pathname to classify.
 * config : RouteConfig
 *     Route configuration with patterns to match against.
 *     Defaults to defaultRouteConfig.
 *
 * Returns
 * -------
 * RouteClassification
 *     Classification result for the route.
 */
export function classifyRoute(
  pathname: string,
  config: RouteConfig = defaultRouteConfig,
): RouteClassification {
  const lowerPathname = pathname.toLowerCase();

  // Check static file extensions
  const isStaticFile = config.staticExtensions.some((ext) =>
    lowerPathname.endsWith(ext),
  );

  // Check public asset prefixes
  const isPublicPrefix = config.publicAssetPrefixes.some((prefix) =>
    pathname.startsWith(prefix),
  );

  // Check API routes
  const isApiRoute = config.apiPrefixes.some((prefix) =>
    pathname.startsWith(prefix),
  );

  // Check auth routes
  const isAuthRoute = config.authPrefixes.some((prefix) =>
    pathname.startsWith(prefix),
  );

  // Check protected routes
  const isProtectedRoute = config.protectedPatterns.some((pattern) =>
    pattern.test(pathname),
  );

  // Check anonymous-allowed routes
  const isAnonymousAllowedPage = config.anonymousAllowedPatterns.some(
    (pattern) => pattern.test(pathname),
  );

  return {
    isApiRoute,
    isAuthRoute,
    isPublicAsset: isPublicPrefix || isStaticFile,
    isProtectedRoute,
    isAnonymousAllowedPage,
    isHomePage: pathname === "/",
  };
}
