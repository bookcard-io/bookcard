import { type NextRequest, NextResponse } from "next/server";
import { getAuthenticatedClient } from "@/services/http/routeHelpers";

/**
 * POST /api/books/upload
 *
 * Proxies request to upload a book file to the backend.
 */
export async function POST(request: NextRequest) {
  try {
    // Read formData first before any other request access
    // to avoid "body already consumed" errors in Next.js
    const formData = await request.formData();
    const file = formData.get("file") as File | null;

    if (!file) {
      return NextResponse.json({ detail: "No file provided" }, { status: 400 });
    }

    // Get authenticated client after reading formData
    // (getAuthenticatedClient only reads cookies, not body)
    const { client, error } = getAuthenticatedClient(request);

    if (error) {
      return error;
    }

    // Convert File to Blob to avoid stream locking issues
    // This creates a fresh copy that can be safely reused
    const fileBlob = await file.arrayBuffer();
    const fileCopy = new File([fileBlob], file.name, {
      type: file.type,
      lastModified: file.lastModified,
    });

    // Create FormData for backend request
    const backendFormData = new FormData();
    backendFormData.append("file", fileCopy);

    // Don't set Content-Type header for FormData - fetch will set it with boundary
    const response = await client.request("/books/upload", {
      method: "POST",
      headers: {}, // Empty headers - fetch will set Content-Type for FormData
      body: backendFormData,
    });

    // Clone response before reading to avoid "body already consumed" errors
    // This ensures the response body can be read safely
    const clonedResponse = response.clone();
    const data = await clonedResponse.json();

    if (!response.ok) {
      return NextResponse.json(
        { detail: data.detail || "Failed to upload book" },
        { status: response.status },
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json(
      {
        detail:
          error instanceof Error ? error.message : "Internal server error",
      },
      { status: 500 },
    );
  }
}
