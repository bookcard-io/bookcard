import { type NextRequest, NextResponse } from "next/server";
import { AUTH_COOKIE_NAME, BACKEND_URL } from "@/constants/config";

/**
 * GET /api/metadata/search
 *
 * Proxies request to search for book metadata from external sources.
 * Supports query parameters: query, locale, max_results_per_provider, provider_ids
 */
export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const { searchParams } = request.nextUrl;
    const query = searchParams.get("query");

    if (!query) {
      return NextResponse.json(
        { detail: "Query parameter is required" },
        { status: 400 },
      );
    }

    const url = new URL(`${BACKEND_URL}/metadata/search`);
    url.searchParams.set("query", query);

    const locale = searchParams.get("locale");
    if (locale) {
      url.searchParams.set("locale", locale);
    }

    const maxResults = searchParams.get("max_results_per_provider");
    if (maxResults) {
      url.searchParams.set("max_results_per_provider", maxResults);
    }

    const providerIds = searchParams.get("provider_ids");
    if (providerIds) {
      url.searchParams.set("provider_ids", providerIds);
    }

    const response = await fetch(url.toString(), {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to search metadata" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}

/**
 * POST /api/metadata/search
 *
 * Proxies request to search for book metadata from external sources.
 * Accepts JSON body with query, locale, max_results_per_provider, provider_ids
 */
export async function POST(request: NextRequest) {
  try {
    const token = request.cookies.get(AUTH_COOKIE_NAME)?.value;

    if (!token) {
      return NextResponse.json({ detail: "Unauthorized" }, { status: 401 });
    }

    const body = await request.json();

    if (!body.query) {
      return NextResponse.json(
        { detail: "Query is required" },
        { status: 400 },
      );
    }

    const url = new URL(`${BACKEND_URL}/metadata/search`);

    const response = await fetch(url.toString(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to search metadata" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
