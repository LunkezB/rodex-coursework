import { ApiError } from "./auth";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type Sex = "male" | "female" | "unknown";

export interface PersonRead {
  id: string;
  owner_id: string;
  surname: string | null;
  given_name: string;
  patronymic: string | null;
  name_variants: string | null;
  sex: Sex;
  birth_date: string | null;
  birth_place: string | null;
  death_date: string | null;
  death_place: string | null;
  notes: string | null;
}

export interface PersonCreate {
  surname?: string | null;
  given_name: string;
  patronymic?: string | null;
  name_variants?: string | null;
  sex?: Sex;
  birth_date?: string | null;
  birth_place?: string | null;
  death_date?: string | null;
  death_place?: string | null;
  notes?: string | null;
}

export interface PersonUpdate {
  surname?: string | null;
  given_name?: string;
  patronymic?: string | null;
  name_variants?: string | null;
  sex?: Sex;
  birth_date?: string | null;
  birth_place?: string | null;
  death_date?: string | null;
  death_place?: string | null;
  notes?: string | null;
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

export async function listPersons(token: string): Promise<PersonRead[]> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/persons`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<PersonRead[]>(res);
}

export async function createPerson(
  token: string,
  payload: PersonCreate,
): Promise<PersonRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/persons`, {
      method: "POST",
      headers: jsonHeaders(token),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<PersonRead>(res);
}

export async function updatePerson(
  token: string,
  personId: string,
  payload: PersonUpdate,
): Promise<PersonRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/persons/${personId}`, {
      method: "PATCH",
      headers: jsonHeaders(token),
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<PersonRead>(res);
}

export async function deletePerson(
  token: string,
  personId: string,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/persons/${personId}`, {
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
