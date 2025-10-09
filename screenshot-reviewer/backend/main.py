"""FastAPI application entry point for the Screenshot Reviewer backend."""

from __future__ import annotations

import asyncio
import logging
import psutil
import os
import re
import signal
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ✅ Use absolute imports since we’re running from project root with `uvicorn backend.main:app`
from backend.routes import categories, lexicon, screenshots, state
from backend.state_manager import load_selection_state, save_selection_state

# ─────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────
def _configure_logging() -> None:
    """Configure logging once, honoring optional DEBUG and LOG_LEVEL settings."""
    debug_enabled = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}
    log_level = os.getenv("LOG_LEVEL", "DEBUG" if debug_enabled else "INFO").upper()
    log_format = os.getenv("LOG_FORMAT", "%(levelname)s [%(name)s] %(message)s")

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=log_level, format=log_format)
    else:
        root_logger.setLevel(log_level)

    logging.getLogger("screenshot_reviewer").debug("Logging configured (DEBUG=%s)", debug_enabled)


_configure_logging()
logger = logging.getLogger("screenshot_reviewer")

# ─────────────────────────────────────────────
# Global Constants
# ─────────────────────────────────────────────
SCREENSHOTS_DIR = Path("/Volumes/990_Pro/Screenshots")
LOCALHOST_ORIGIN_REGEX = re.compile(r"^https?://(localhost|0\.0\.0\.0)(:\d+)?$", re.IGNORECASE)

# ─────────────────────────────────────────────
# Graceful Shutdown Handler
# ─────────────────────────────────────────────
async def _handle_exit(sig: signal.Signals | int) -> None:
    """Handle shutdown signals gracefully and trigger async save."""
    sig_name = getattr(sig, "name", sig)
    logger.info("📴 Received %s, saving state", sig_name)
    await save_selection_state()

# ─────────────────────────────────────────────
# Lifespan Events
# ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Application startup")
    load_selection_state()

    try:
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(_handle_exit(s)))
            except NotImplementedError:
                logger.debug("Signal %s unsupported in this environment", sig)
    except RuntimeError:
        logger.debug("No running event loop available for signal handlers")

    yield
    logger.info("🛑 Application shutdown")
    await save_selection_state()

# ─────────────────────────────────────────────
# CORS Configuration
# ─────────────────────────────────────────────
def _sanitize_origins(raw_value: str) -> list[str]:
    items = [origin.strip() for origin in raw_value.split(",") if origin.strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for origin in items:
        if origin not in seen:
            seen.add(origin)
            unique.append(origin)
    return unique


def _build_cors_config() -> tuple[list[str], str | None]:
    raw = os.getenv("ALLOWED_ORIGINS", "")
    explicit = _sanitize_origins(raw)
    if not explicit or "*" in explicit:
        return ["*"], LOCALHOST_ORIGIN_REGEX.pattern
    return explicit, LOCALHOST_ORIGIN_REGEX.pattern

# ─────────────────────────────────────────────
# App Factory
# ─────────────────────────────────────────────
def _create_app() -> FastAPI:
    allow_origins, allow_origin_regex = _build_cors_config()

    app = FastAPI(
        title="Screenshot Reviewer API",
        version="2.1.0",
        lifespan=lifespan,
    )
    app.debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}

    cors_kwargs = dict(
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if allow_origin_regex:
        cors_kwargs["allow_origin_regex"] = allow_origin_regex

    app.router.redirect_slashes = True
    app.router.redirect_trailing_slash = True  # ✅ add this line

    app.add_middleware(CORSMiddleware, **cors_kwargs)

    # ✅ Include routers
    app.include_router(screenshots.router, prefix="/api/screenshots", tags=["screenshots"])
    app.include_router(categories.router, prefix="/api/categories", tags=["categories"])
    app.include_router(lexicon.router, prefix="/api/lexicon", tags=["lexicon"])
    app.include_router(state.router, prefix="/api/state", tags=["state"])

    # ✅ Serve static screenshots
    if SCREENSHOTS_DIR.exists():
        app.mount("/files", StaticFiles(directory=SCREENSHOTS_DIR), name="files")

    # ✅ Healthcheck
    @app.get("/api/health")
    def healthcheck():
        return {"status": "ok"}

    # ✅ Serve frontend build if available
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

    return app

async def _handle_exit(sig: signal.Signals | int) -> None:
    sig_name = getattr(sig, "name", sig)
    logger.info("📴 Received %s, saving state and cleaning up", sig_name)
    await save_selection_state()
    try:
        # Auto-kill any other uvicorn processes bound to same port
        current_pid = os.getpid()
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            if "uvicorn" in (proc.info["name"] or "") and proc.info["pid"] != current_pid:
                proc.kill()
                logger.info("💀 Terminated lingering uvicorn PID %s", proc.info["pid"])
    except Exception as e:
        logger.warning("Cleanup failed: %s", e)


# ─────────────────────────────────────────────
# App Instance
# ─────────────────────────────────────────────
app = _create_app()