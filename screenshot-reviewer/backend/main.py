from fastapi import FastAPI
from routes import screenshots, categories

app = FastAPI(title="Screenshot Reviewer API")

app.include_router(screenshots.router, prefix="/api/screenshots", tags=["Screenshots"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])

@app.get("/")
def read_root():
    return {"message": "Screenshot Reviewer API running"}
