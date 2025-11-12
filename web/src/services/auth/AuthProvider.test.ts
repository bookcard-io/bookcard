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
import { BearerAuthProvider, createBearerAuthProvider } from "./AuthProvider";

describe("AuthProvider", () => {
  describe("BearerAuthProvider", () => {
    it("should return Bearer token when token is provided", () => {
      const provider = new BearerAuthProvider("test-token");
      expect(provider.getAuthHeader()).toBe("Bearer test-token");
    });

    it("should return null when token is null", () => {
      const provider = new BearerAuthProvider(null);
      expect(provider.getAuthHeader()).toBeNull();
    });

    it("should return null when token is undefined", () => {
      const provider = new BearerAuthProvider(undefined);
      expect(provider.getAuthHeader()).toBeNull();
    });

    it("should return null when token is empty string", () => {
      const provider = new BearerAuthProvider("");
      expect(provider.getAuthHeader()).toBeNull();
    });
  });

  describe("createBearerAuthProvider", () => {
    it("should create BearerAuthProvider with token", () => {
      const provider = createBearerAuthProvider("test-token");
      expect(provider).toBeInstanceOf(BearerAuthProvider);
      expect(provider.getAuthHeader()).toBe("Bearer test-token");
    });

    it("should create BearerAuthProvider with null token", () => {
      const provider = createBearerAuthProvider(null);
      expect(provider).toBeInstanceOf(BearerAuthProvider);
      expect(provider.getAuthHeader()).toBeNull();
    });

    it("should create BearerAuthProvider with undefined token", () => {
      const provider = createBearerAuthProvider(undefined);
      expect(provider).toBeInstanceOf(BearerAuthProvider);
      expect(provider.getAuthHeader()).toBeNull();
    });
  });
});
