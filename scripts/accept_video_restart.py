"""Real OS-process restart acceptance, exclusively on a production copy.

Run from the repository root using the locked backend Python environment.
No production migration or production write is performed by this script.
"""

import argparse
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
from contextlib import closing
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / ".workspace" / "e2e"


def hashes(paths):
    result = {}
    for path in paths:
        with path.open("rb") as stream:
            result[str(path.resolve())] = hashlib.file_digest(stream, "sha256").hexdigest()
    return result


def snapshot(source, bootstrap):
    paths = sorted(p for p in source.rglob("*") if p.is_file())
    assert source.is_dir() and (source / "data/workspace.db").is_file()
    return hashes([*paths, bootstrap, ROOT / "HANDOFF.md"])


def revision(path):
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
        assert db.execute("pragma integrity_check").fetchone()[0] == "ok"
        assert db.execute("pragma foreign_key_check").fetchall() == []
        return db.execute("select version_num from alembic_version").fetchone()[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--bootstrap", type=Path, required=True)
    args = parser.parse_args()
    source, bootstrap = args.source.resolve(), args.bootstrap.resolve()
    assert Path(json.loads(bootstrap.read_text())["workspace_root"]).resolve() == source
    before = snapshot(source, bootstrap)
    assert revision(source / "data/workspace.db") == "0009_storyboards"
    BOUNDARY.mkdir(parents=True, exist_ok=True)
    run = Path(tempfile.mkdtemp(prefix="phase10-restart-", dir=BOUNDARY)).resolve()
    assert run.parent == BOUNDARY.resolve() and not source.is_relative_to(run)
    evidence = ROOT / ".workspace" / "phase10" / run.name
    evidence.mkdir(parents=True)
    (evidence / "before.json").write_text(json.dumps(before, indent=2))
    report = {"workspace": str(run), "processes": [], "result": "FAIL"}
    process = None
    log = None
    primary = None
    cleanup_failures = []

    def stop():
        nonlocal process, log
        if process is None:
            return
        try:
            if process.poll() is None:
                process.stdin.write(b"stop\n")
                process.stdin.flush()
            code = process.wait(timeout=30)
            assert code == 0, f"Backend graceful shutdown exit={code}"
        finally:
            try:
                if process.poll() is None:
                    # Emergency teardown never turns a failed graceful exit into PASS.
                    process.kill()
                    process.wait(timeout=10)
            finally:
                report["processes"][-1]["exit_code"] = process.poll()
                try:
                    process.stdin.close()
                finally:
                    if log:
                        log.close()
                if process.poll() is not None:
                    process = None

    try:
        workspace = run / "workspace"
        shutil.copytree(source, workspace)
        for old, digest in before.items():
            old = Path(old)
            if old.is_relative_to(source):
                copied = workspace / old.relative_to(source)
                assert hashes([copied])[str(copied)] == digest, str(copied)
        config = run / "config.json"
        config.write_text(json.dumps({"workspace_root": str(workspace)}))
        env = {
            **os.environ,
            "AVW_BOOTSTRAP_CONFIG_PATH": str(config),
            "AVW_WORKSPACE_ROOT": str(workspace),
            "AVW_E2E_RUN_DIRECTORY": str(run),
            "PYTHONIOENCODING": "utf-8",
        }
        subprocess.run(
            [sys.executable, str(ROOT / "scripts/make_test_media.py")], env=env, check=True
        )
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        address = f"http://127.0.0.1:{port}/api"

        def request(path, method="GET", data=None, raw=None):
            body = (
                raw if raw is not None else json.dumps(data).encode() if data is not None else None
            )
            req = Request(address + path, data=body, method=method)
            if data is not None:
                req.add_header("Content-Type", "application/json")
            try:
                with urlopen(req, timeout=20) as response:
                    content = response.read()
                    if response.headers.get_content_type() == "application/json":
                        return json.loads(content)
                    return content
            except HTTPError as exc:
                exc.close()
                raise

        def start():
            nonlocal process, log
            number = len(report["processes"]) + 1
            log = (evidence / f"process-{number}.log").open("w", encoding="utf-8")
            process = subprocess.Popen(
                [sys.executable, "-m", "test_support.restart_server", "--port", str(port)],
                cwd=ROOT / "backend",
                env=env,
                stdin=subprocess.PIPE,
                stdout=log,
                stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            report["processes"].append({"pid": process.pid, "exit_code": None})
            for _ in range(150):
                assert process.poll() is None, "Backend exited during startup"
                try:
                    if request("/health")["status"] == "ok":
                        assert revision(workspace / "data/workspace.db") == "0010_video_results"
                        return
                except (URLError, ConnectionError, TimeoutError):
                    pass
                time.sleep(0.1)
            raise AssertionError("Backend startup timed out")

        start()
        projects = request("/projects")
        project = next(p for p in projects if p["name"].startswith("SPF"))
        shot = next(
            s for s in request(f"/projects/{project['id']}/shots") if s["shot_code"] == "S13"
        )
        assert shot["duration_seconds"] == 10
        report["shot_id"] = shot["id"]
        path = f"/shots/{shot['id']}"
        request(
            "/settings/ai",
            "PUT",
            {
                "api_base_url": "https://unused.invalid/v1",
                "model": "fake-model",
                "api_key": "fake-restart-key",
            },
        )
        template = request(
            "/prompt-templates",
            "POST",
            {
                "name": "Restart acceptance " + str(uuid4()),
                "scope": "PROJECT",
                "project_id": project["id"],
                "category": "VIDEO_GENERATION",
                "template_content": "{{shot_context}}",
            },
        )
        preview = request(path + "/prompts/preview", "POST", {"template_id": template["id"]})
        prompt = request(
            path + "/prompts/generate",
            "POST",
            {
                "template_id": template["id"],
                "input_hash": preview["input_hash"],
                "operation_id": str(uuid4()),
            },
        )
        storyboard = request(
            path + "/storyboards/import?filename=storyboard.png",
            "POST",
            raw=(run / "fixtures/storyboard.png").read_bytes(),
        )
        media = (run / "fixtures/video.mp4").read_bytes()
        versions = []
        for version in (1, 2):
            query = urlencode(
                {
                    "filename": "video.mp4",
                    "source_storyboard_id": storyboard["id"],
                    "source_prompt_record_id": prompt["id"],
                    "notes": f"Restart V{version} 视频备注",
                }
            )
            record = request(path + "/video-results/import?" + query, "POST", raw=media)
            assert record["version"] == version and record["is_selected"]
            versions.append(record)
        history = request(path + "/video-results")
        assert [r["version"] for r in history] == [2, 1]
        assert [r["is_selected"] for r in history] == [True, False]
        request(f"/video-results/{versions[0]['id']}/select", "POST")
        before_restart = request(path + "/video-results")
        assert [r["is_selected"] for r in before_restart] == [False, True]
        stop()
        start()
        assert report["processes"][0]["pid"] != report["processes"][1]["pid"]
        after_restart = request(path + "/video-results")
        assert after_restart == before_restart, "History changed after independent process restart"
        for record in after_restart:
            assert record["notes"] == f"Restart V{record['version']} 视频备注"
            assert record["source_storyboard_id"] == storyboard["id"]
            assert record["source_prompt_record_id"] == prompt["id"]
            asset = request(f"/assets/{record['asset_id']}")
            assert asset["asset_type"] == "VIDEO"
            assert project["id"] in [p["id"] for p in asset["projects"]]
            assert shot["id"] in [s["id"] for s in asset["shots"]]
            assert request(f"/assets/{asset['id']}/file") == media
            assert request(f"/assets/{asset['id']}/thumbnail").startswith(b"\xff\xd8")
        stop()
        report["business_assertions"] = "PASS"
    except BaseException as exc:
        primary = exc
        report["primary_failure"] = traceback.format_exc()
    finally:
        try:
            stop()
        except BaseException:
            cleanup_failures.append(traceback.format_exc())
        try:
            if log:
                log.close()
            assert process is None, "Backend still running; retain isolated workspace"
            # Validate the exact deletion target; never follow a replaced root.
            assert run.resolve() == run and not run.is_symlink()
            assert run.parent == BOUNDARY.resolve() and run.name.startswith("phase10-restart-")
            shutil.rmtree(run)
            report["isolated_workspace_removed"] = not run.exists()
        except BaseException:
            cleanup_failures.append(traceback.format_exc())
        try:
            after = snapshot(source, bootstrap)
            report["production_hashes_unchanged"] = before == after
            report["protected_files"] = len(after)
            report["production_revision"] = revision(source / "data/workspace.db")
            (evidence / "after.json").write_text(json.dumps(after, indent=2))
            assert before == after, "PRODUCTION HASH CHANGED"
            assert report["production_revision"] == "0009_storyboards"
        except BaseException:
            report["verification_failure"] = traceback.format_exc()
        report["cleanup_failures"] = cleanup_failures
        report["residual_isolated_directory"] = run.exists()
        if primary is None and not cleanup_failures and "verification_failure" not in report:
            report["result"] = "PASS"
        try:
            (evidence / "result.json").write_text(json.dumps(report, indent=2))
        except BaseException:
            report["result"] = "FAIL"
            report["report_failure"] = traceback.format_exc()
        print(json.dumps(report, indent=2))
    if primary is not None:
        raise primary
    assert report["result"] == "PASS"


if __name__ == "__main__":
    main()
