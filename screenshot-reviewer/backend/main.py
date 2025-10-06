"""FastAPI application entry point for the Screenshot Reviewer backend."""

from __future__ import annotations
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import categories, lexicon, screenshots

app = FastAPI(title="Screenshot Reviewer API", version="2.0.0")

# ✅ Load allowed origins from environment or fallback to "*"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if "*" not in ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include routers
app.include_router(screenshots.router, prefix="/api/screenshots", tags=["Screenshots"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
app.include_router(lexicon.router, prefix="/api/lexicon", tags=["Lexicon"])

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