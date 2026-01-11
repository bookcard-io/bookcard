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

import { afterEach, describe, expect, it, vi } from "vitest";
import { InvalidUrlError, SSRFError } from "@/types/imageProbe";

vi.mock("node:dns/promises", () => ({
  lookup: vi.fn(),
}));

import { lookup } from "node:dns/promises";
import { validateRemoteHttpUrl } from "./ssrf";

const ALLOWED_SCHEMES = new Set<"http" | "https">(["http", "https"]);

type DnsLookupAll = (
  hostname: string,
  options: { all: true; verbatim: true },
) => Promise<Array<{ address: string; family: number }>>;

function mockLookupAll(resolved: Array<{ address: string; family: number }>) {
  (
    lookup as unknown as ReturnType<typeof vi.fn<DnsLookupAll>>
  ).mockResolvedValue(resolved);
}

/**
 * Validate a URL using the standard allowlist.
 *
 * Parameters
 * ----------
 * url : string
 *     URL to validate.
 */
async function validate(url: string) {
  return await validateRemoteHttpUrl(url, { allowedSchemes: ALLOWED_SCHEMES });
}

describe("ssrf utils", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe("validateRemoteHttpUrl", () => {
    it.each([
      { url: "not-a-url", error: InvalidUrlError },
      { url: "file:///etc/passwd", error: InvalidUrlError },
      { url: "ftp://example.com/image.jpg", error: InvalidUrlError },
    ])("should reject invalid URL '$url'", async ({ url, error }) => {
      await expect(validate(url)).rejects.toBeInstanceOf(error);
    });

    it.each([
      { url: "http://localhost/image.jpg" },
      { url: "http://metadata.google.internal/latest/meta-data" },
      { url: "http://metadata/" },
    ])("should reject blocked hostname '$url'", async ({ url }) => {
      await expect(validate(url)).rejects.toBeInstanceOf(SSRFError);
    });

    it.each([
      { url: "http://127.0.0.1/image.jpg" },
      { url: "http://127.0.0.2/image.jpg" },
      { url: "http://10.0.0.1/image.jpg" },
      { url: "http://172.16.0.1/image.jpg" },
      { url: "http://192.168.1.1/image.jpg" },
      { url: "http://169.254.169.254/latest/meta-data/" },
      { url: "http://0.0.0.0/image.jpg" },
      { url: "http://224.0.0.1/image.jpg" },
      // IPv6 literals must be bracketed in URLs.
      { url: "http://[::1]/image.jpg" },
      { url: "http://[fc00::1]/image.jpg" },
      { url: "http://[fe80::1]/image.jpg" },
      { url: "http://[::]/image.jpg" },
    ])("should reject private/local IP literal '$url'", async ({ url }) => {
      await expect(validate(url)).rejects.toBeInstanceOf(SSRFError);
      expect(lookup).not.toHaveBeenCalled();
    });

    it("should allow public IP literals without DNS lookup", async () => {
      const result = await validate("https://8.8.8.8/image.jpg");
      expect(result.hostname).toBe("8.8.8.8");
      expect(lookup).not.toHaveBeenCalled();
    });

    it("should reject hostnames resolving to private IPs", async () => {
      // `lookup` has overloads; in our code we always call it with `{ all: true }`,
      // which resolves to an array of records.
      mockLookupAll([{ address: "192.168.1.10", family: 4 }]);

      await expect(
        validate("https://example.com/image.jpg"),
      ).rejects.toBeInstanceOf(SSRFError);

      expect(lookup).toHaveBeenCalledWith("example.com", {
        all: true,
        verbatim: true,
      });
    });

    it("should allow hostnames resolving to public IPs", async () => {
      mockLookupAll([{ address: "93.184.216.34", family: 4 }]);

      const result = await validate("https://example.com/image.jpg");
      expect(result.hostname).toBe("example.com");
    });
  });
});
