import { defineConfig, devices } from "@playwright/test";
import { resolve } from "node:path";

const dev = process.env.AVW_E2E_MODE === "dev";
const python =
  process.platform === "win32"
    ? "../backend/.venv/Scripts/python.exe"
    : "../backend/.venv/bin/python";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: dev ? "http://127.0.0.1:5174" : "http://127.0.0.1:8766",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    env: {
      AVW_WORKSPACE_ROOT: resolve("../.workspace/e2e/workspace"),
      AVW_BOOTSTRAP_CONFIG_PATH: resolve("../.workspace/e2e/config.json"),
    },
    command: `"${python}" ../scripts/start.py --no-browser --port 8766${dev ? " --dev --frontend-port 5174" : ""}`,
    url: dev ? "http://127.0.0.1:5174" : "http://127.0.0.1:8766",
    reuseExistingServer: false,
    timeout: 45_000,
    gracefulShutdown: { signal: "SIGTERM", timeout: 5_000 },
  },
});
