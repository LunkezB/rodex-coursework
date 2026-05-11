import { ApiError } from "./auth";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type ParentRole = "father" | "mother" | "unknown";

export interface RelationshipRead {
  id: string;
  owner_id: string;
  parent_id: string;
  child_id: string;
  kind: string;
  parent_role: ParentRole;
}

export interface RelationshipCreate {
  parent_id: string;
  child_id: string;
  parent_role: ParentRole;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.ok) {
    return res.json() as Promise<T>;
  }
  let detail = `HTTP ${res.status}`;
  try {
    const body = (await res.json()) as { detail?: string };
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // ignore parse errors
  }
  throw new ApiError(res.status, detail);
}

function jsonHeaders(token: string): HeadersInit {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function listRelationships(
  token: string,
): Promise<RelationshipRead[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/relationships`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<RelationshipRead[]>(res);
}

export async function createRelationship(
  token: string,
  payload: RelationshipCreate,
): Promise<RelationshipRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/relationships`, {
      method: "POST",
      headers: jsonHeaders(token),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<RelationshipRead>(res);
}

export async function deleteRelationship(
  token: string,
  relationshipId: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/relationships/${relationshipId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }
}
