"""Guarded E2E Uvicorn process with a stdin-controlled graceful shutdown."""

import argparse
import sys
import threading

import uvicorn


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True, type=int)
    args = parser.parse_args()
    server = uvicorn.Server(
        uvicorn.Config("test_support.e2e_app:app", host="127.0.0.1", port=args.port)
    )

    def shutdown():
        # EOF also shuts down if the acceptance driver exits unexpectedly.
        sys.stdin.readline()
        server.should_exit = True

    threading.Thread(target=shutdown, daemon=True).start()
    server.run()


if __name__ == "__main__":
    main()
