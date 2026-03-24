export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, data: unknown) {
    super(`API Error ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

export function useApi() {
  const config = useRuntimeConfig();
  const auth = useAuthStore();
  const base = config.public.apiBase as string;

  async function apiFetch<T>(path: string, opts?: RequestInit): Promise<T> {
    const headers = new Headers(opts?.headers);
    if (opts?.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    if (auth.apiKey) {
      headers.set("X-API-Key", auth.apiKey);
    }

    const response = await fetch(`${base}${path}`, {
      ...opts,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: response.statusText,
      }));
      throw new ApiError(response.status, error);
    }

    return response.json() as Promise<T>;
  }

  return { apiFetch };
}
