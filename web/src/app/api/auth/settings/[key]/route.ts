import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * PUT /api/auth/settings/[key]
 *
 * Proxies request to upsert a user setting.
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ key: string }> },
) {
  try {
    const { key } = await params;
    const body = await request.json();

    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    const response = await client.request(
      `/auth/settings/${encodeURIComponent(key)}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      },
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to update setting" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in PUT /api/auth/settings/[key]:", error);
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 },
    );
  }
}
