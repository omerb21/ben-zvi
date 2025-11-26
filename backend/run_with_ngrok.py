from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


PORT = 8000


def _find_ngrok_executable(base_dir: Path) -> Path:
    """Locate ngrok.exe relative to the backend directory.

    Expected layout (recommended):

    backend/
      run_with_ngrok.py
      ngrok/
        ngrok.exe
    """

    candidates = [
        base_dir / "ngrok" / "ngrok.exe",
        base_dir.parent / "ngrok" / "ngrok.exe",
    ]

    for candidate in candidates:
        if candidate.is_file():
            return candidate

    raise FileNotFoundError(
        "Could not find ngrok.exe. Place it under 'ngrok/ngrok.exe' "
        "next to this backend folder."
    )


def _wait_for_ngrok_public_url(timeout_seconds: float = 30.0) -> str | None:
    """Poll ngrok's local API until a public https URL is available."""

    deadline = time.time() + timeout_seconds
    api_url = "http://127.0.0.1:4040/api/tunnels"

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(api_url) as resp:  # type: ignore[call-arg]
                data = json.load(resp)
            tunnels = data.get("tunnels", []) or []
            for tunnel in tunnels:
                url = tunnel.get("public_url")
                if isinstance(url, str) and url.startswith("https://"):
                    return url
        except Exception:
            time.sleep(1.0)

    return None


def main() -> int:
    base_dir = Path(__file__).resolve().parent

    try:
        ngrok_path = _find_ngrok_executable(base_dir)
    except FileNotFoundError as exc:  # pragma: no cover - helper script
        print(str(exc))
        input("Press Enter to exit...")
        return 1

    print(f"Starting ngrok from: {ngrok_path}")

    ngrok_env = os.environ.copy()
    ngrok_proc = subprocess.Popen(
        [str(ngrok_path), "http", str(PORT)],
        cwd=str(base_dir),
        env=ngrok_env,
    )

    print("Waiting for ngrok public URL...")
    public_url = _wait_for_ngrok_public_url()

    backend_env = os.environ.copy()
    if public_url:
        print(f"Detected PUBLIC_BASE_URL: {public_url}")
        backend_env["PUBLIC_BASE_URL"] = public_url
    else:
        print(
            "WARNING: Could not detect ngrok public URL from http://127.0.0.1:4040. "
            "Client links will use localhost."
        )

    print("Starting FastAPI backend with uvicorn...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", str(PORT)],
        cwd=str(base_dir),
        env=backend_env,
    )

    # Optionally start the frontend dev server (Vite) if the frontend
    # directory exists. This is best-effort only: if Node/npm are not
    # available or the command fails, we simply log a warning and keep
    # the backend + ngrok running.
    frontend_proc: subprocess.Popen | None = None
    frontend_dir = base_dir.parent / "frontend"
    if frontend_dir.is_dir():
        try:
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            print(f"Starting frontend dev server in: {frontend_dir}")
            frontend_proc = subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=str(frontend_dir),
                env=os.environ.copy(),
            )
        except Exception as exc:  # pragma: no cover - helper script
            print(f"WARNING: Failed to start frontend dev server: {exc}")

    print("Backend, ngrok, and (optionally) frontend are running.")
    print("Close this window or press Ctrl+C to stop all.")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:  # pragma: no cover - manual interrupt
        pass
    finally:
        try:
            backend_proc.terminate()
        except Exception:
            pass
        if frontend_proc is not None:
            try:
                frontend_proc.terminate()
            except Exception:
                pass
        try:
            ngrok_proc.terminate()
        except Exception:
            pass

    return 0


if __name__ == "__main__":  # pragma: no cover - script entrypoint
    raise SystemExit(main())
