"""FastAPI application entry point for the Screenshot Reviewer backend."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import categories, lexicon, screenshots

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

SCREENSHOTS_DIR = Path("/Volumes/990_Pro/Screenshots")

LOCALHOST_ORIGIN_REGEX = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", re.IGNORECASE)


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


allow_origins, allow_origin_regex = _build_cors_config()

cors_kwargs = dict(
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
if allow_origin_regex:
    cors_kwargs["allow_origin_regex"] = allow_origin_regex

app = FastAPI(title="Screenshot Reviewer API", version="2.0.0")
app.debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes"}

app.add_middleware(CORSMiddleware, **cors_kwargs)

# ✅ Include routers
app.include_router(screenshots.router, prefix="/api/screenshots", tags=["Screenshots"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(lexicon.router, prefix="/api/lexicon", tags=["Lexicon"])

if SCREENSHOTS_DIR.exists():
    app.mount("/files", StaticFiles(directory=SCREENSHOTS_DIR), name="files")

@app.get("/api/health")
def healthcheck():
    return {"status": "ok"}

# ✅ Serve frontend if built
frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount(
        "/",
        StaticFiles(directory=frontend_dist, html=True),
        name="frontend",
    )
