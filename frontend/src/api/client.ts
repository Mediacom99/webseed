const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

export const customFetch = async <T>(
  url: string,
  options?: RequestInit,
): Promise<T> => {
  const apiKey = localStorage.getItem("webseed-api-key");

  const headers = new Headers(options?.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (apiKey) {
    headers.set("X-API-Key", apiKey);
  }

  const response = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({
      detail: response.statusText,
    }));
    throw new ApiError(response.status, error);
  }

  return response.json() as Promise<T>;
};

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

export type ErrorType<Error> = Error;
export type BodyType<BodyData> = BodyData;

export default customFetch;
