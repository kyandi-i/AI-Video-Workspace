export async function getJson(path: string): Promise<unknown> {
  return requestJson(path);
}

export async function requestJson<T>(
  path: string,
  method = "GET",
  data?: unknown,
  file?: Blob,
  timeoutMs?: number,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      signal: AbortSignal.timeout(timeoutMs ?? (file ? 300_000 : 8_000)),
      method,
      headers: file
        ? { "Content-Type": "application/octet-stream" }
        : data === undefined
          ? undefined
          : { "Content-Type": "application/json" },
      body: file ?? (data === undefined ? undefined : JSON.stringify(data)),
    });
  } catch {
    throw new Error("无法连接本地服务，请确认服务运行后重试。");
  }
  if (!response.ok) {
    let message = "本地服务暂时无法完成操作，请稍后重试。";
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

export const isMissingEntity = (error: Error | null) =>
  error instanceof ApiError && error.status === 404;
