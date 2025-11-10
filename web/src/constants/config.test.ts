import { afterEach, describe, expect, it, vi } from "vitest";

describe("config", () => {
  const originalEnv = process.env;

  afterEach(() => {
    process.env = originalEnv;
    vi.resetModules();
  });

  it("should use BACKEND_URL from environment", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "https://custom-backend:8000",
      NODE_ENV: "test",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("https://custom-backend:8000");
  });

  it("should use NEXT_PUBLIC_BACKEND_URL if BACKEND_URL is not set", async () => {
    process.env = {
      ...originalEnv,
      NEXT_PUBLIC_BACKEND_URL: "https://public-backend:8000",
      NODE_ENV: "test",
    };
    delete process.env.BACKEND_URL;
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("https://public-backend:8000");
  });

  it("should prepend http:// if URL doesn't start with http:// or https://", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "localhost:8000",
      NODE_ENV: "test",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("http://localhost:8000");
  });

  it("should trim whitespace from URL", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "  https://backend:8000  ",
      NODE_ENV: "test",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("https://backend:8000");
  });

  it("should replace https:// with http:// for localhost in development", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "https://localhost:8000",
      NODE_ENV: "development",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("http://localhost:8000");
  });

  it("should replace https:// with http:// for 127.0.0.1 in development", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "https://127.0.0.1:8000",
      NODE_ENV: "development",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("http://127.0.0.1:8000");
  });

  it("should not replace https:// for localhost in production", async () => {
    process.env = {
      ...originalEnv,
      BACKEND_URL: "https://localhost:8000",
      NODE_ENV: "production",
    };
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("https://localhost:8000");
  });

  it("should use default production URL when no env vars are set", async () => {
    process.env = {
      ...originalEnv,
      NODE_ENV: "production",
    };
    delete process.env.BACKEND_URL;
    delete process.env.NEXT_PUBLIC_BACKEND_URL;
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("http://fundamental-backend:8000");
  });

  it("should use default development URL when no env vars are set", async () => {
    process.env = {
      ...originalEnv,
      NODE_ENV: "development",
    };
    delete process.env.BACKEND_URL;
    delete process.env.NEXT_PUBLIC_BACKEND_URL;
    vi.resetModules();
    const { BACKEND_URL } = await import("./config");
    expect(BACKEND_URL).toBe("http://localhost:8000");
  });

  it("should set COOKIE_SECURE to true in production", async () => {
    process.env = {
      ...originalEnv,
      NODE_ENV: "production",
    };
    vi.resetModules();
    const { COOKIE_SECURE } = await import("./config");
    expect(COOKIE_SECURE).toBe(true);
  });

  it("should set COOKIE_SECURE to false in development", async () => {
    process.env = {
      ...originalEnv,
      NODE_ENV: "development",
    };
    vi.resetModules();
    const { COOKIE_SECURE } = await import("./config");
    expect(COOKIE_SECURE).toBe(false);
  });
});
