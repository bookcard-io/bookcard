export interface BasicConfig {
  allow_anonymous_browsing: boolean;
  allow_public_registration: boolean;
  require_email_for_registration: boolean;
  max_upload_size_mb: number;
}

export type BasicConfigUpdate = Partial<BasicConfig>;

export async function fetchBasicConfig(): Promise<BasicConfig> {
  const response = await fetch("/api/admin/basic-config", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to fetch config" }));
    throw new Error(error.detail || "Failed to fetch config");
  }

  return response.json();
}

export async function updateBasicConfig(
  payload: BasicConfigUpdate,
): Promise<BasicConfig> {
  const response = await fetch("/api/admin/basic-config", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to update config" }));
    throw new Error(error.detail || "Failed to update config");
  }

  return response.json();
}

export async function fetchPublicBasicConfig(): Promise<BasicConfig> {
  const response = await fetch("/api/config/anonymous-browsing", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: "Failed to fetch public config" }));
    throw new Error(error.detail || "Failed to fetch public config");
  }

  return response.json();
}
