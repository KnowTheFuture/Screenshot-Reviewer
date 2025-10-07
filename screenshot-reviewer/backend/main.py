"""FastAPI application entry point for the Screenshot Reviewer backend."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import categories, lexicon, screenshots, state
from .state_manager import load_selection_state, save_selection_state


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

SCREENSHOTS_DIR = Path("/Volumes/990_Pro/Screenshots")
LOCALHOST_ORIGIN_REGEX = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", re.IGNORECASE)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Application startup")
    load_selection_state()
    yield
    logger.info("🛑 Application shutdown")
    await save_selection_state()


def _handle_exit(sig, _frame) -> None:
    """Handle shutdown signals gracefully and trigger async save."""
    import signal

    # Resolve signal name safely (works for both enum and int)
    sig_name = getattr(sig, "name", None)
    if sig_name is None:
        try:
            sig_name = next((n for n, v in signal.__dict__.items() if v == sig), str(sig))
        except Exception:
            sig_name = str(sig)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("No running event loop to handle signal %s", sig_name)
        return

    if loop.is_closed():
        logger.debug("Event loop already closed; skipping save for %s", sig_name)
        return

    logger.info("📴 Received signal %s, scheduling state save", sig_name)
    loop.create_task(save_selection_state())


# Register signal handlers if possible (ignored in unsupported environments)
try:  # pragma: no cover - platform dependent
    signal.signal(signal.SIGINT, _handle_exit)
    signal.signal(signal.SIGTERM, _handle_exit)
except (ValueError, RuntimeError):
    logger.debug("Signal handlers already registered or unsupported")


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
    if not explicit:
        return ["*"], LOCALHOST_ORIGIN_REGEX.pattern
    if "*" in explicit:
        return ["*"], LOCALHOST_ORIGIN_REGEX.pattern
    # Respect explicit origins but still allow any localhost / 127.0.0.1 via regex.
    return explicit, LOCALHOST_ORIGIN_REGEX.pattern


def _create_app() -> FastAPI:
    allow_origins, allow_origin_regex = _build_cors_config()

    app_instance = FastAPI(title="Screenshot Reviewer API", version="2.0.0", lifespan=lifespan)
    app_instance.debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}

    cors_kwargs = dict(
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    if allow_origin_regex:
        cors_kwargs["allow_origin_regex"] = allow_origin_regex

    app_instance.add_middleware(CORSMiddleware, **cors_kwargs)

    # ✅ Include routers
    app_instance.include_router(screenshots.router, prefix="/api/screenshots", tags=["Screenshots"])
    app_instance.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
    app_instance.include_router(lexicon.router, prefix="/api/lexicon", tags=["Lexicon"])
    app_instance.include_router(state.router, tags=["State"])

    if SCREENSHOTS_DIR.exists():
        app_instance.mount("/files", StaticFiles(directory=SCREENSHOTS_DIR), name="files")

    @app_instance.get("/api/health")
    def healthcheck():
        return {"status": "ok"}

    # ✅ Serve frontend if built
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    if frontend_dist.exists():
        app_instance.mount(
            "/",
            StaticFiles(directory=frontend_dist, html=True),
            name="frontend",
        )

    return app_instance


app = _create_app()
