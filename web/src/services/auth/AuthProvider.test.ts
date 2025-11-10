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
