import { execFileSync } from "node:child_process";
import { resolve } from "node:path";

export default function setup() {
  const python = resolve(
    process.platform === "win32"
      ? "../backend/.venv/Scripts/python.exe"
      : "../backend/.venv/bin/python",
  );
  execFileSync(python, [resolve("../scripts/make_test_media.py")], {
    stdio: "inherit",
  });
}
