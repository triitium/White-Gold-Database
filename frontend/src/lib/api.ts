import { readCookie } from "./cookies";

const API_BASE =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

type ApiOptions = RequestInit & {
  csrf?: boolean;
};

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parseError(response: Response): Promise<string> {
  try {
    const body = await response.json();

    if (typeof body?.detail === "string") {
      return body.detail;
    }

    if (body?.detail) {
      return JSON.stringify(body.detail);
    }
  } catch {
    // fall through
  }

  return `${response.status} ${response.statusText}`;
}

export async function api<T>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (options.csrf) {
    const token = readCookie("csrf_token");

    if (!token) {
      throw new ApiError(403, "Missing CSRF token");
    }

    headers.set("X-CSRF-Token", token);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers,
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      await parseError(response),
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const apiBaseUrl = API_BASE;
