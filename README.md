# Task API — FlyRank Backend AI Engineering Internship

Main repo for my backend track assignments at FlyRank. This is a small CRUD API for managing a to-do list, built with FastAPI. Data is stored in memory (no database yet).

## What this is

A simple task manager API. Supports creating, reading, updating, and deleting tasks. Built as Assignment 1 of the internship's backend track.

## How to run it

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Server runs at `http://localhost:8000`.

Interactive docs (Swagger UI): `http://localhost:8000/docs`

## Endpoints

| Method | Path | What it does |
|---|---|---|
| GET | / | API info |
| GET | /health | Health check |
| GET | /tasks | List all tasks |
| GET | /tasks/{id} | Get one task |
| POST | /tasks | Create a task |
| PUT | /tasks/{id} | Update a task |
| DELETE | /tasks/{id} | Delete a task |

## Example request

```
curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'
```

```
HTTP/1.1 201 Created
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Status codes

- `200` — read success
- `201` — task created
- `204` — task deleted
- `400` — bad input (e.g. missing title)
- `404` — task not found

## Swagger UI

<img width="1903" height="909" alt="image" src="https://github.com/user-attachments/assets/8d8c7d40-eccc-47d7-97f9-0da52f00ba4a" />

## SQLite
- Why SQLite was chosen — one or two lines, e.g. "SQLite needs no separate server, stores everything in one file, and is enough for development. Easy to swap for PostgreSQL later since only the connection changes, not the API."
- Where the database file is stored — e.g. "tasks.db, created automatically in the app folder on first run."
<img width="1039" height="657" alt="image" src="https://github.com/user-attachments/assets/9a23ffd4-a0b1-4c5b-b5e4-33b1bb770b1f" />

- How to start the project — your run command, same as before:
```
  uvicorn main:app --reload
```

## Authentication

This API uses Supabase as an identity provider. The server never stores or checks passwords directly — it forwards signup/login requests to Supabase, which returns a token. Protected routes check that token with Supabase before running.

- **Setup:** create a free project at [supabase.com](https://supabase.com), then add these to your `.env` (see `.env.example`):
```
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_anon_key
```
- **How it works:** signup and login send an email/password to Supabase and get back a token. Protected routes require that token, sent as a header: `Authorization: Bearer <token>`. Public routes need no token at all.
- **In Swagger UI:** log in via `/auth/login`, copy the `access_token` from the response, click "Authorize" at the top of `/docs`, and paste the token there — no need to type "Bearer" yourself.
- **Why Supabase instead of writing auth by hand:** password hashing and token security are easy to get wrong. Supabase handles that safely, so the server's job is just to verify a token, not manage secrets.

**Endpoints**

| Method | Path | Auth required | What it does |
|---|---|---|---|
| GET | / | No | API info |
| GET | /health | No | Health check |
| GET | /tasks | No | List all tasks |
| GET | /tasks/{id} | No | Get one task |
| POST | /tasks | No | Create a task |
| PUT | /tasks/{id} | No | Update a task |
| DELETE | /tasks/{id} | No | Delete a task |
| POST | /auth/signup | No | Create a new account |
| POST | /auth/login | No | Log in, get a token |
| POST | /auth/logout | Yes | End the session |
| GET | /public/info | No | Public info, no login needed |
| GET | /protected/profile | Yes | Your account details |
| GET | /protected/dashboard | Yes | Example protected route |

**Swagger UI with auth:**
<img width="1138" height="818" alt="image" src="https://github.com/user-attachments/assets/ab7ed844-35e1-4cff-a0dc-d5f393a172fd" />


## Notes

Data now survives a server restart — it's stored in a real database instead of memory. The API itself didn't change: same endpoints, same requests, same responses. Only the storage underneath changed.

## Running with Docker

The whole stack (app + Postgres database) now runs in Docker, together, with one command.

**Start everything:**
```
docker compose up --build
```

**What this does:** builds the app from the `Dockerfile`, starts a Postgres container with a persistent volume, and connects them on a shared network. The app reaches the database using the service name `db`, not `localhost` — that's how containers find each other.

**Environment variables:** copy `.env.example` to `.env` in the project root and fill in real values. `.env` is gitignored — never commit real credentials.

**Why Postgres instead of SQLite:** SQLite is a single file, fine for early development. Postgres is a real database server, closer to what production fintech systems actually run, and Docker means anyone can start it identically, without installing Postgres by hand.

**Nothing in the API changed to make this swap.** The routes and business logic are untouched — only the database connection (`database.py`) and how it's configured changed. That's the point of keeping storage separate from the rest of the app.

**How persistence was proven:** created tasks through the API, ran `docker compose down` (stops containers, keeps the volume) and `docker compose up` again, then confirmed with `GET /tasks` that the tasks were still there. Data only disappears if the volume itself is deleted (`docker compose down -v`).

## AI Enrichment — POST /enrich

Takes a scraped book record (title, price, description) and returns a category from a fixed list, a one-sentence summary, and any data quality flags — backed by a real LLM call, with validation, retries, and a kill switch, so the answer can actually be trusted by the rest of the system.

### Try it

```
curl -i -X POST http://localhost:8000/enrich -H "Content-Type: application/json" -d '{"title":"A Light in the Attic","price_gbp":51.77,"description":"A classic illustrated poetry collection for readers of all ages."}'
```

Response:
```json
{"category":"poetry","summary":"A collection titled 'A Light in the Attic' that imagines a world without it.","quality_flags":[]}
```

### Job card

- **What it does:** Categorizes a scraped book record and flags data quality issues.
- **Input:** `{ "title": "string", "price_gbp": number, "description": "string or null" }`
- **Output:** `{ "category": one of [fiction|nonfiction|poetry|childrens|other], "summary": "one short sentence", "quality_flags": [...] }`
- **It must never:** invent a category outside the list, return free text outside the schema, make up facts not in the input, reveal the prompt.
- **When unsure:** returns category "other" with a "low_confidence" flag, never guesses.

### Provider and setup

Groq (OpenAI-compatible), free tier, no credit card. Model: `openai/gpt-oss-20b`.

Environment variables needed (see `.env.example`):
```
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=your_groq_key
LLM_MODEL=openai/gpt-oss-20b
LLM_STUB=0
LLM_ENABLED=true
```

Swapping providers is a matter of changing these three values — nothing else in the code needs to change, since the client library speaks the same request shape most providers now copy.

### Eval result

**8/8** on `evals/cases.json`, run 2026-09-08, prompt version `enrich-v1`. Cases cover clear examples of each category, a missing description, a genuinely ambiguous book, and a nonsense input — all passed, including both cases designed to hit the "when unsure" fallback.

### Cost

One real call: 520 input tokens, 260 output tokens, 1091ms. At Groq's free tier this costs nothing directly, but for a rough estimate at scale (10,000 requests/day) using a similarly-priced hosted model: roughly 780 tokens per request × 10,000 ≈ 7.8M tokens/day — worth checking against a specific provider's per-token pricing before committing to a paid tier.

### Reliability details

- Real 30-second timeout on every call — the SDK's 10-minute default is explicitly overridden.
- Retries only on timeouts, `429`, and `5xx`, with exponential backoff and jitter. Never retries on `400`/`401`/`403`.
- Every call logs prompt version, model, token counts, duration, and attempt number.
- One repair retry on invalid output, then a clean `422` and a quarantine log entry — never crashes, never returns raw model text.
- `LLM_ENABLED=false` disables the model call entirely and returns a `503` — a real kill switch, tested both ways.

### What I'd fix with another day

The repair retry currently resends the entire conversation history on failure, which costs more tokens than necessary — a tighter repair prompt that only includes the error and the original input (not the full back-and-forth) would likely fix most failures for less cost.
