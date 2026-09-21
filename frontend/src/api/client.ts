export async function getJson(path: string): Promise<unknown> {
  return requestJson(path);
}

export async function requestJson<T>(
  path: string,
  method = "GET",
  data?: unknown,
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    signal: AbortSignal.timeout(8_000),
    method,
    headers:
      data === undefined ? undefined : { "Content-Type": "application/json" },
    body: data === undefined ? undefined : JSON.stringify(data),
  });
  if (!response.ok) {
    let message = `本地服务返回错误（${response.status}）`;
    let code = `HTTP_${response.status}`;
    try {
      const body = (await response.json()) as {
        message?: string;
        code?: string;
      };
      message = body.message || message;
      code = body.code || code;
    } catch {
      /* A proxy failure may not return JSON. */
    }
    throw new ApiError(message, response.status, code);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}
