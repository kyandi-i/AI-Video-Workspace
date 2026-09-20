export async function getJson(path: string): Promise<unknown> {
  const response = await fetch(`/api${path}`, {
    signal: AbortSignal.timeout(8_000),
  });
  if (!response.ok) {
    let message = `本地服务返回错误（${response.status}）`;
    try {
      const body = (await response.json()) as { message?: string };
      message = body.message || message;
    } catch {
      /* A proxy failure may not return JSON. */
    }
    throw new Error(message);
  }
  return response.json();
}
