#!/usr/bin/env python3
"""Unified dev runner for backend and frontend with auto-restart."""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from threading import Thread

from colorama import Fore, Style, init
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

init(autoreset=True)
load_dotenv()

BACKEND_CMD = [
    "uvicorn",
    "backend.main:app",
    "--reload",
    "--port",
    os.getenv("BACKEND_PORT", "8000"),
]
FRONTEND_CMD = ["npm", "run", "dev"]
FRONTEND_CWD = Path("frontend")
WATCH_PATH = Path("backend")


def stream(proc: subprocess.Popen[str], label: str, color: str) -> None:
    for line in proc.stdout:  # type: ignore[attr-defined]
        print(f"{color}[{label}]{Style.RESET_ALL} {line}", end="")


def launch(name: str, cmd: list[str], cwd: Path | None = None, color: str = Fore.WHITE) -> subprocess.Popen[str]:
    process = subprocess.Popen(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    Thread(target=stream, args=(process, name, color), daemon=True).start()
    return process


def main() -> None:
    print(Fore.CYAN + "\n🚀 Starting unified dev environment...\n")
    backend = launch("backend", BACKEND_CMD, color=Fore.GREEN)
    time.sleep(2)
    frontend = launch("frontend", FRONTEND_CMD, FRONTEND_CWD, color=Fore.MAGENTA)

    def restart_backend() -> None:
        nonlocal backend
        print(Fore.YELLOW + "\n♻️  Restarting backend...")
        backend.terminate()
        backend.wait()
        backend = launch("backend", BACKEND_CMD, color=Fore.GREEN)

    class Watch(FileSystemEventHandler):
        def on_any_event(self, event):  # type: ignore[override]
            if not getattr(event, "is_directory", False):
                restart_backend()

    shutting_down = False

    observer = Observer()
    observer.schedule(Watch(), str(WATCH_PATH), recursive=True)
    observer.start()

    def shutdown(*_args) -> None:
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        print(Fore.RED + "\n🛑 Shutting down...")
        observer.stop()
        backend.terminate()
        frontend.terminate()
        backend.wait()
        frontend.wait()
        print(Fore.CYAN + "✅ All processes stopped cleanly.")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while observer.is_alive():
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
    finally:
        observer.join()


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as exc:
        print(Fore.RED + f"Required command missing: {exc}")
        sys.exit(1)
