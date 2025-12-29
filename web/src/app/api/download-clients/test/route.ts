import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * POST /api/download-clients/test
 * Test connection with provided settings.
 */
export async function POST(request: NextRequest) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const body = await request.json();

    const response = await client.request("/download-clients/test", {
      method: "POST",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Connection test failed" },
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
