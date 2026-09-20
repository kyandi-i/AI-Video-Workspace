/* global process */

import { mkdirSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const browserPath = "D:\\study\\DO\\DevCache\\playwright";
const cli = resolve(projectRoot, "node_modules/@playwright/test/cli.js");

mkdirSync(browserPath, { recursive: true });
const result = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], {
  cwd: projectRoot,
  env: { ...process.env, PLAYWRIGHT_BROWSERS_PATH: browserPath },
  stdio: "inherit",
  windowsVerbatimArguments: false,
});

if (result.error) throw result.error;
process.exit(result.status ?? 1);
