# Screenshot Reviewer (React + FastAPI)

A full-stack application for batching, tagging, and reviewing thousands of screenshots. The frontend is built with React, Vite, and TailwindCSS; the backend is FastAPI serving JSON-backed APIs.

## Features

- Paginated grid (50 per page) with batch selection and category drag/assign.
- Category sidebar with add/edit/delete and live counts.
- Toolbar filters (All, Pending, Deferred, Low confidence, Re-review), search, and progress indicators.
- Screenshot details modal with tags, summary, confidence slider, delete & re-review toggles.
- Lexicon builder panel for keyword→tag mappings with live suggestions.
- Batch operations for category assignment and deletion.
- Timestamp group navigation for context-aware review.

## Project Structure

```
screenshot-reviewer/
├── backend/
│   ├── main.py              # FastAPI app factory
│   ├── models.py            # Pydantic models
│   ├── routes/              # API routers (screenshots, categories, lexicon)
│   ├── storage.py           # JSON persistence helpers
│   ├── data/                # JSON “database” files
│   └── seed_data.py         # CLI seeder (python backend/seed_data.py)
├── frontend/
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.cjs
│   ├── postcss.config.cjs
│   └── src/
│       ├── api/client.js
│       ├── App.jsx
│       ├── main.jsx
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       ├── store/
│       └── styles/
├── requirements.txt         # Backend dependencies
└── README.md
```

## Getting Started

### 1. Backend setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python backend/seed_data.py
uvicorn backend.main:app --reload
```

Backend runs on http://127.0.0.1:8000 and exposes:
- `GET /api/screenshots` (with `page`, `page_size`, `filter`, `category`, `search`, `group_id` query params)
- `GET/PUT /api/screenshots/{id}`
- `POST /api/screenshots/batch`
- `GET/POST/PUT/DELETE /api/categories`
- `GET/POST/DELETE /api/lexicon`
- `GET /api/health`

### 2. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server boots on http://127.0.0.1:5173 and proxies API calls to FastAPI.

### 3. Build for production

```bash
cd frontend
npm run build
```

The compiled assets live in `frontend/dist/`. When this folder exists the FastAPI app automatically serves it as the default site.

## Testing

- Backend: add pytest tests under `backend/tests/` (not included by default).
- Frontend: integrate your favourite test runner (Vitest, Jest) as needed.

## Data Files

- `backend/data/screenshots.json`
- `backend/data/categories.json`
- `backend/data/lexicon.json`

All writes are atomic and safe for local development. Backups can be created manually before large edits.

## Keyboard Shortcuts

- `←` / `→` — navigate pagination
- `Enter` — go to next page
- `Ctrl+S` / `Cmd+S` — reserved for save hooks (wire up per modal)

Enjoy faster screenshot triage!
