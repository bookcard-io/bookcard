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

/**
 * Route configuration for middleware.
 *
 * Follows OCP by allowing route patterns to be extended without modifying
 * the core matching logic. Follows SoC by centralizing route definitions.
 */
export interface RouteConfig {
  /** Regex patterns for routes that require authentication. */
  protectedPatterns: RegExp[];
  /** Regex patterns for routes allowed for anonymous users when enabled. */
  anonymousAllowedPatterns: RegExp[];
  /** File extensions considered static assets. */
  staticExtensions: string[];
  /** URL prefixes considered public assets. */
  publicAssetPrefixes: string[];
  /** URL prefixes for API routes. */
  apiPrefixes: string[];
  /** URL prefixes for authentication routes. */
  authPrefixes: string[];
}

/**
 * Route classification result.
 *
 * Follows SRP by encapsulating route classification state.
 */
export interface RouteClassification {
  isApiRoute: boolean;
  isAuthRoute: boolean;
  isPublicAsset: boolean;
  isProtectedRoute: boolean;
  isAnonymousAllowedPage: boolean;
  isHomePage: boolean;
}

/**
 * Response from anonymous browsing configuration API.
 */
export interface AnonymousBrowsingResponse {
  allow_anonymous_browsing: boolean;
}
