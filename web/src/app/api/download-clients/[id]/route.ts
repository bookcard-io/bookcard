import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * GET /api/download-clients/[id]
 * Get a download client by ID.
 */
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const { id } = await params;
    const response = await client.request(`/download-clients/${id}`, {
      method: "GET",
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to fetch download client" },
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
 * PUT /api/download-clients/[id]
 * Update a download client.
 */
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const { id } = await params;
    const body = await request.json();

    const response = await client.request(`/download-clients/${id}`, {
      method: "PUT",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to update download client" },
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
 * DELETE /api/download-clients/[id]
 * Delete a download client.
 */
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> },
) {
  try {
    const { client, error } = getAuthenticatedClient(request);
    if (error) {
      return error;
    }

    const { id } = await params;
    const response = await client.request(`/download-clients/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      // 204 No Content has no body
      if (response.status === 204) {
        return new NextResponse(null, { status: 204 });
      }

      // Try to parse error body if not 204
      try {
        const data = await response.json();
        return NextResponse.json(
          { detail: data.detail || "Failed to delete download client" },
          { status: response.status },
        );
      } catch {
        return NextResponse.json(
          { detail: "Failed to delete download client" },
          { status: response.status },
        );
      }
    }

    return new NextResponse(null, { status: 204 });
  } catch {
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 },
    );
  }
}
