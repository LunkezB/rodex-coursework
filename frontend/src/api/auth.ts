const BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export interface UserRead {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  full_name?: string | null;
}

export interface LoginPayload {
  email: string;
  password: string;
}

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
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
    // ignore parse error, keep generic message
  }
  throw new ApiError(res.status, detail);
}

export async function register(payload: RegisterPayload): Promise<UserRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<UserRead>(res);
}

export async function login(payload: LoginPayload): Promise<string> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  const data = await handleResponse<TokenResponse>(res);
  return data.access_token;
}

export async function getMe(token: string): Promise<UserRead> {
  let res: Response;
  try {
    res = await fetch(`${BASE}/api/v1/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  } catch {
    throw new ApiError(0, "Backend недоступен");
  }
  return handleResponse<UserRead>(res);
}
