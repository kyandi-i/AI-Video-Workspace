/* global process */

import { mkdirSync, mkdtempSync, realpathSync, rmSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { basename, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const browserPath = "D:\\study\\DO\\DevCache\\playwright";
const cli = resolve(projectRoot, "node_modules/@playwright/test/cli.js");

mkdirSync(browserPath, { recursive: true });
const testParent = resolve(projectRoot, "../.workspace/e2e");
let runDirectory;
if (process.argv[2] === "test") {
  mkdirSync(testParent, { recursive: true });
  runDirectory = mkdtempSync(resolve(testParent, "run-"));
}
const result = spawnSync(process.execPath, [cli, ...process.argv.slice(2)], {
  cwd: projectRoot,
  env: {
    ...process.env,
    PLAYWRIGHT_BROWSERS_PATH: browserPath,
    ...(runDirectory ? { AVW_E2E_RUN_DIRECTORY: runDirectory } : {}),
  },
  stdio: "inherit",
  windowsVerbatimArguments: false,
});

// Playwright has stopped its servers at this point. Remove only this run's
// generated workspace (DB, copies, thumbnails, temporary files and fixtures).
if (runDirectory && result.status === 0) {
  const target = realpathSync(runDirectory);
  if (
    dirname(target) !== realpathSync(testParent) ||
    !basename(target).startsWith("run-")
  ) {
    throw new Error("Refusing cleanup outside the generated E2E workspace");
  }
  rmSync(target, { recursive: true, maxRetries: 3, retryDelay: 200 });
}

if (result.error) throw result.error;
process.exit(result.status ?? 1);
