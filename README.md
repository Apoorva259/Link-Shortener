# snip:// — URL Shortener

A full-stack URL shortener: FastAPI backend + SQLite storage + a browser frontend, ready to deploy on Render.

## What's inside

```
url-shortener/
├── main.py            # FastAPI app: shorten, redirect, stats, list
├── requirements.txt   # Python dependencies
├── render.yaml         # Render deploy config
├── static/
│   └── index.html      # Frontend (single file, no build step)
└── .gitignore
```

## How it works

- `POST /api/shorten` — takes `{"url": "...", "custom_code": "optional"}`, returns a short code
- `GET /{code}` — redirects to the original URL and increments its click count
- `GET /api/stats/{code}` — click count + metadata for one code
- `GET /api/urls` — last 100 shortened links (powers the "Recent links" list on the homepage)
- `static/index.html` is served at `/` — it's a plain HTML/CSS/JS page that calls the API above

Codes are random 6-character alphanumeric strings, or a custom code if you provide one and it's not taken.

## Deploy — no local setup needed

### 1. Push this folder to GitHub

Easiest way from the browser, no git installed locally:

1. Go to [github.com/new](https://github.com/new), create a new repo (e.g. `url-shortener`), keep it empty (no README/gitignore).
2. On the new repo's page, click **"uploading an existing file"**.
3. Drag in every file from this folder (keep the `static/` folder structure — drag the whole folder in, or create `static/index.html` manually via "Add file → Create new file" and paste the contents).
4. Commit directly to `main`.

### 2. Connect to Render

1. Go to [dashboard.render.com](https://dashboard.render.com) → **New → Web Service**.
2. Connect your GitHub account and pick the `url-shortener` repo.
3. Render should auto-detect `render.yaml` and pre-fill the settings. If not, set manually:
   - **Environment**: Python 3
   - **Build command**: `pip install -r requirements.txt`
   - **Start command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Choose the **Free** instance type, click **Create Web Service**.
5. Wait for the build/deploy logs to finish — Render gives you a live URL like `https://url-shortener-xxxx.onrender.com`.

Open that URL and you'll see the shortener homepage, live.

### 3. Important: the free plan's disk is not persistent

Render's free web services use an **ephemeral filesystem** — the SQLite file (`shortener.db`) resets to empty every time the service restarts, redeploys, or spins down from inactivity. That's fine for a portfolio demo, but don't rely on it to keep links long-term. Two ways to fix this later if you want:

- **Render Persistent Disk** (paid plans only) — mount a disk and point `DB_PATH` at it.
- **Swap SQLite for a hosted Postgres** — Render's free Postgres tier persists properly; would need a small code change from `sqlite3` to something like `asyncpg` or `SQLAlchemy`. Happy to help with that migration if you want the links to actually survive.

## Local testing (optional)

If you ever do want to run it locally:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Then visit `http://localhost:8000`.
