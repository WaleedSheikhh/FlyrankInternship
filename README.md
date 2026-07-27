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

## Notes

Data resets on server restart — it's stored in memory only. Database support comes in a later assignment.
