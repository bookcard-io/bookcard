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

import { describe, expect, it } from "vitest";
import { getProfilePictureUrlWithCacheBuster } from "./profile";

describe("profile utils", () => {
  describe("getProfilePictureUrlWithCacheBuster", () => {
    it("should generate profile picture URL with default cache buster", () => {
      const url = getProfilePictureUrlWithCacheBuster();
      expect(url).toMatch(/^\/api\/auth\/profile-picture\?v=\d+$/);
    });

    it("should generate profile picture URL with custom cache buster", () => {
      const cacheBuster = 1234567890;
      const url = getProfilePictureUrlWithCacheBuster(cacheBuster);
      expect(url).toBe("/api/auth/profile-picture?v=1234567890");
    });

    it("should generate different URLs for different cache busters", () => {
      const url1 = getProfilePictureUrlWithCacheBuster(1000);
      const url2 = getProfilePictureUrlWithCacheBuster(2000);
      expect(url1).toBe("/api/auth/profile-picture?v=1000");
      expect(url2).toBe("/api/auth/profile-picture?v=2000");
      expect(url1).not.toBe(url2);
    });
  });
});
