"""Start the local application and own the complete child-process lifecycle."""

import argparse
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]


def check_port(port: int) -> None:
    if not 1 <= port <= 65535:
        raise RuntimeError(f"Invalid port: {port}")
    with socket.socket() as probe:
        try:
            probe.bind(("127.0.0.1", port))
        except OSError as exc:
            raise RuntimeError(f"Port {port} is in use. Choose another port.") from exc


def launch(command: list[str], cwd: Path, env: dict[str, str]) -> subprocess.Popen:
    options = {"cwd": cwd, "env": env, "stdout": sys.stdout, "stderr": sys.stderr}
    if os.name == "nt":
        options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    else:
        options["start_new_session"] = True
    return subprocess.Popen(command, **options)


def stop(process: subprocess.Popen) -> None:
    if os.name == "nt":
        if process.poll() is None:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        if os.name != "nt":
            os.killpg(process.pid, signal.SIGKILL)
        else:
            process.kill()
        process.wait()


def wait_ready(url: str, processes: list[subprocess.Popen], health: bool = False) -> None:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if any(p.poll() is not None for p in processes):
            raise RuntimeError("A service exited during startup. See its output above.")
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    if not health or json.load(response).get("app") == "ai-video-workspace":
                        return
        except (URLError, TimeoutError, ConnectionError):
            pass
        time.sleep(0.2)
    raise RuntimeError(f"Timed out waiting for {url}")


def main(*, app_import: str = "app.main:app") -> int:
    parser = argparse.ArgumentParser(description="Run AI Video Workspace locally.")
    parser.add_argument("--dev", action="store_true", help="Run Vite and backend with live reload")
    parser.add_argument("--port", type=int, default=8765, help="Backend port (default: 8765)")
    parser.add_argument("--frontend-port", type=int, default=5173)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    processes: list[subprocess.Popen] = []

    def interrupted(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, interrupted)
    try:
        check_port(args.port)
        if args.dev:
            if args.port == args.frontend_port:
                raise RuntimeError("Backend and frontend ports must be different.")
            check_port(args.frontend_port)
            if not (ROOT / "frontend/node_modules/vite/bin/vite.js").is_file():
                raise RuntimeError("Missing frontend dependencies. Run npm ci in frontend first.")
            if not shutil.which("node"):
                raise RuntimeError("Node.js is required for development mode.")
        elif not (ROOT / "frontend/dist/index.html").is_file():
            raise RuntimeError("Frontend build missing. Run npm ci and npm run build in frontend.")

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["AVW_API_TARGET"] = f"http://127.0.0.1:{args.port}"
        backend = [
            sys.executable,
            "-m",
            "uvicorn",
            app_import,
            "--host",
            "127.0.0.1",
            "--port",
            str(args.port),
        ]
        if args.dev:
            backend.append("--reload")
        processes.append(launch(backend, ROOT / "backend", env))
        wait_ready(f"{env['AVW_API_TARGET']}/api/health", processes, health=True)
        address = env["AVW_API_TARGET"]
        if args.dev:
            processes.append(
                launch(
                    [
                        shutil.which("node"),
                        "node_modules/vite/bin/vite.js",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        str(args.frontend_port),
                        "--strictPort",
                    ],
                    ROOT / "frontend",
                    env,
                )
            )
            address = f"http://127.0.0.1:{args.frontend_port}"
        wait_ready(address, processes)
        print(f"\nAI Video Workspace: {address}\nPress Ctrl+C to stop.\n", flush=True)
        if not args.no_browser:
            webbrowser.open(address)
        while all(p.poll() is None for p in processes):
            time.sleep(0.4)
        raise RuntimeError("A service stopped unexpectedly. See its output above.")
    except KeyboardInterrupt:
        print("\nStopping local services...", flush=True)
        return 0
    except (RuntimeError, OSError) as exc:
        print(f"Startup failed: {exc}", file=sys.stderr)
        return 1
    finally:
        for process in reversed(processes):
            stop(process)


if __name__ == "__main__":
    raise SystemExit(main())
