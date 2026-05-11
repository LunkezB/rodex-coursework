import { ApiError } from "./auth";

const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export type SosaPersonSex = "male" | "female" | "unknown";

export interface SosaPerson {
  id: string;
  surname: string | null;
  given_name: string;
  patronymic: string | null;
  sex: SosaPersonSex;
  birth_date: string | null;
  birth_place: string | null;
  death_date: string | null;
  death_place: string | null;
}

export interface SosaReportPerson {
  sosa_number: number;
  person: SosaPerson;
}

export interface SosaGeneration {
  generation: number;
  persons: SosaReportPerson[];
}

export interface SosaReport {
  proband_id: string;
  max_depth: number;
  generations: SosaGeneration[];
  warnings: string[];
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

export async function getSosaReport(
  token: string,
  probandId: string,
  maxDepth: number,
): Promise<SosaReport> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/reports/sosa/${probandId}?max_depth=${maxDepth}`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<SosaReport>(res);
}

export async function downloadSosaCsv(
  token: string,
  probandId: string,
  maxDepth: number,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(
      `${BASE}/api/v1/reports/sosa/${probandId}/export.csv?max_depth=${maxDepth}`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
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
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `sosa-report-${probandId}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
