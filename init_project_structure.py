import os
from pathlib import Path

# Define the folder structure
structure = {
    "screenshot-reviewer": {
        "backend": {
            "routes": {
                "screenshots.py": "",
                "categories.py": "",
            },
            "data": {
                "screenshots.json": "{}\n",
                "categories.json": "{}\n",
            },
            "main.py": '''from fastapi import FastAPI
from routes import screenshots, categories

app = FastAPI(title="Screenshot Reviewer API")

app.include_router(screenshots.router, prefix="/api/screenshots", tags=["Screenshots"])
app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])

@app.get("/")
def read_root():
    return {"message": "Screenshot Reviewer API running"}
''',
            "models.py": '''from pydantic import BaseModel
from typing import List, Optional

class Screenshot(BaseModel):
    id: str
    path: str
    tags: List[str] = []
    summary: Optional[str] = None
    category: Optional[str] = None
    confidence: float = 0.0

class Category(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
''',
        },
        "frontend": {
            "src": {
                "components": {
                    "Sidebar.jsx": "export default function Sidebar() { return <div>Sidebar</div>; }\n",
                    "ScreenshotGrid.jsx": "export default function ScreenshotGrid() { return <div>ScreenshotGrid</div>; }\n",
                    "CategoryManager.jsx": "export default function CategoryManager() { return <div>CategoryManager</div>; }\n",
                    "Toolbar.jsx": "export default function Toolbar() { return <div>Toolbar</div>; }\n",
                },
                "api": {
                    "client.js": '''import axios from "axios";
const api = axios.create({ baseURL: "http://localhost:8000/api" });
export default api;
''',
                },
                "pages": {
                    "Home.jsx": '''export default function Home() { return <div>Home Page</div>; }\n''',
                },
                "App.jsx": '''import Home from "./pages/Home";
export default function App() { return <Home />; }
''',
            },
            "public": {},
            "package.json": '''{
  "name": "screenshot-reviewer-frontend",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "vite": "^4.4.0",
    "@vitejs/plugin-react": "^4.0.0"
  }
}
''',
        },
        "README.md": "# Screenshot Reviewer\n\nReact + FastAPI app for managing and tagging screenshots.",
        ".gitignore": """# Python
__pycache__/
*.pyc
.venv/
env/

# Node
node_modules/
dist/
build/

# Screenshots
*.png
*.jpg
*.jpeg
!frontend/public/**/*.png

# System
.DS_Store
""",
        "requirements.txt": "fastapi\nuvicorn\npydantic\n",
    }
}

def create_structure(base_path, tree):
    for name, content in tree.items():
        path = Path(base_path) / name
        if isinstance(content, dict):
            path.mkdir(exist_ok=True)
            create_structure(path, content)
        else:
            if not path.exists():
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"✅ Created file: {path}")
            else:
                print(f"⚙️ Skipped existing file: {path}")

if __name__ == "__main__":
    base = Path(".")
    create_structure(base, structure)
    print("\n🎉 Project scaffold complete!")