import { ApiError } from "./auth";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface SourceRead {
  id: string;
  owner_id: string;
  title: string;
  archive_reference: string | null;
  url: string | null;
  reliability_comment: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface SourceCreate {
  title: string;
  archive_reference?: string | null;
  url?: string | null;
  reliability_comment?: string | null;
  notes?: string | null;
}

export interface SourceUpdate {
  title?: string;
  archive_reference?: string | null;
  url?: string | null;
  reliability_comment?: string | null;
  notes?: string | null;
}

export interface PersonSourceRead {
  id: string;
  person_id: string;
  source_id: string;
  comment: string | null;
  created_at: string;
  updated_at: string;
}

export interface RelationshipSourceRead {
  id: string;
  relationship_id: string;
  source_id: string;
  comment: string | null;
  created_at: string;
  updated_at: string;
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

async function handleNoContent(res: Response): Promise<void> {
  if (res.ok) return;
  let detail = `HTTP ${res.status}`;
  try {
    const body = (await res.json()) as { detail?: string };
    if (typeof body.detail === "string") detail = body.detail;
  } catch {
    // ignore
  }
  throw new ApiError(res.status, detail);
}

export async function listSources(token: string): Promise<SourceRead[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<SourceRead[]>(res);
}

export async function listPersonSourceLinks(
  token: string,
): Promise<PersonSourceRead[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources/person-links`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<PersonSourceRead[]>(res);
}

export async function listRelationshipSourceLinks(
  token: string,
): Promise<RelationshipSourceRead[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources/relationship-links`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<RelationshipSourceRead[]>(res);
}

export async function createSource(
  token: string,
  payload: SourceCreate,
): Promise<SourceRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources`, {
      method: "POST",
      headers: jsonHeaders(token),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<SourceRead>(res);
}

export async function updateSource(
  token: string,
  sourceId: string,
  payload: SourceUpdate,
): Promise<SourceRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources/${sourceId}`, {
      method: "PATCH",
      headers: jsonHeaders(token),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<SourceRead>(res);
}

export async function deleteSource(
  token: string,
  sourceId: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/sources/${sourceId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleNoContent(res);
}

export async function linkSourceToPerson(
  token: string,
  sourceId: string,
  personId: string,
): Promise<PersonSourceRead> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/sources/${sourceId}/persons/${personId}`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<PersonSourceRead>(res);
}

export async function unlinkSourceFromPerson(
  token: string,
  sourceId: string,
  personId: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/sources/${sourceId}/persons/${personId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleNoContent(res);
}

export async function linkSourceToRelationship(
  token: string,
  sourceId: string,
  relationshipId: string,
): Promise<RelationshipSourceRead> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/sources/${sourceId}/relationships/${relationshipId}`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<RelationshipSourceRead>(res);
}

export async function unlinkSourceFromRelationship(
  token: string,
  sourceId: string,
  relationshipId: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/sources/${sourceId}/relationships/${relationshipId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      },
    );
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleNoContent(res);
}
