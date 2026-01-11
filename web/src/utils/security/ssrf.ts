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

import { lookup } from "node:dns/promises";
import { isIP } from "node:net";

import { InvalidUrlError, SSRFError } from "@/types/imageProbe";

export interface ValidateRemoteUrlOptions {
  allowedSchemes: ReadonlySet<"http" | "https">;
}

const BLOCKED_HOSTNAMES = new Set([
  "localhost",
  "metadata",
  "metadata.google.internal",
  "metadata.google",
]);

/**
 * Validate that a URL is an external http(s) URL and reject common SSRF targets.
 *
 * This performs:
 * - Scheme allowlisting
 * - Blocklist of well-known internal hostnames
 * - Blocking for IP literals in private / loopback / link-local ranges
 * - DNS resolution and blocking if any resolved IP is private
 *
 * Parameters
 * ----------
 * rawUrl : string
 *     Input URL to validate.
 * options : ValidateRemoteUrlOptions
 *     Validation options.
 *
 * Returns
 * -------
 * URL
 *     Parsed URL if allowed.
 */
export async function validateRemoteHttpUrl(
  rawUrl: string,
  options: ValidateRemoteUrlOptions,
): Promise<URL> {
  const parsed = parseUrl(rawUrl);
  validateScheme(parsed, options.allowedSchemes);

  const hostname = normalizeHostname(parsed.hostname.toLowerCase());
  if (BLOCKED_HOSTNAMES.has(hostname)) {
    throw new SSRFError(`Access to ${hostname} is forbidden`);
  }

  const ipKind = isIP(hostname);
  if (ipKind !== 0) {
    if (isPrivateIpLiteral(hostname)) {
      throw new SSRFError("Access to private or local IP ranges is forbidden");
    }
    return parsed;
  }

  // DNS resolution: reject if hostname resolves to any private/local IP.
  // NOTE: This mitigates (but does not fully eliminate) DNS rebinding risks.
  const records = await lookup(hostname, { all: true, verbatim: true });
  for (const r of records) {
    if (isPrivateIpLiteral(r.address)) {
      throw new SSRFError("Hostname resolves to a private or local IP");
    }
  }

  return parsed;
}

function parseUrl(rawUrl: string): URL {
  try {
    return new URL(rawUrl);
  } catch (error) {
    throw new InvalidUrlError("Malformed URL", error);
  }
}

function validateScheme(
  url: URL,
  allowedSchemes: ReadonlySet<"http" | "https">,
): void {
  const proto = url.protocol.toLowerCase();
  if (proto !== "http:" && proto !== "https:") {
    throw new InvalidUrlError(`Protocol ${url.protocol} not allowed`);
  }

  const scheme = proto.slice(0, -1) as "http" | "https";
  if (!allowedSchemes.has(scheme)) {
    throw new InvalidUrlError(`Scheme ${scheme} not allowed`);
  }
}

function isPrivateIpLiteral(ip: string): boolean {
  // IPv6
  if (ip.includes(":")) {
    const normalized = ip.toLowerCase();

    if (normalized === "::" || normalized === "::1") return true; // unspecified/loopback
    if (normalized.startsWith("fc") || normalized.startsWith("fd")) return true; // fc00::/7 unique local
    if (
      normalized.startsWith("fe8") ||
      normalized.startsWith("fe9") ||
      normalized.startsWith("fea") ||
      normalized.startsWith("feb")
    ) {
      return true; // fe80::/10 link-local
    }

    // IPv4-mapped IPv6: ::ffff:127.0.0.1
    const v4MappedPrefix = "::ffff:";
    if (normalized.startsWith(v4MappedPrefix)) {
      const v4 = normalized.slice(v4MappedPrefix.length);
      return isPrivateIpv4(v4);
    }

    return false;
  }

  // IPv4
  return isPrivateIpv4(ip);
}

function isPrivateIpv4(ip: string): boolean {
  const parts = ip.split(".");
  if (parts.length !== 4) return true;

  const nums = parts.map((p) => Number(p));
  if (nums.some((n) => Number.isNaN(n) || n < 0 || n > 255)) return true;

  const a = nums[0];
  const b = nums[1];
  if (a === undefined || b === undefined) return true;

  // 0.0.0.0/8
  if (a === 0) return true;
  // 127.0.0.0/8
  if (a === 127) return true;
  // 10.0.0.0/8
  if (a === 10) return true;
  // 169.254.0.0/16 (incl. 169.254.169.254 metadata)
  if (a === 169 && b === 254) return true;
  // 172.16.0.0/12
  if (a === 172 && b >= 16 && b <= 31) return true;
  // 192.168.0.0/16
  if (a === 192 && b === 168) return true;
  // 100.64.0.0/10 (carrier-grade NAT)
  if (a === 100 && b >= 64 && b <= 127) return true;
  // 198.18.0.0/15 (benchmarking)
  if (a === 198 && (b === 18 || b === 19)) return true;
  // Multicast 224.0.0.0/4 and reserved 240.0.0.0/4
  if (a >= 224) return true;

  return false;
}

function normalizeHostname(hostname: string): string {
  // Node's WHATWG URL keeps brackets for IPv6 literals in `hostname` (e.g. "[::1]").
  if (hostname.startsWith("[") && hostname.endsWith("]")) {
    return hostname.slice(1, -1);
  }
  return hostname;
}
