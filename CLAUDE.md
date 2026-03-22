# FastAPI Learning Project

## Role
Claude is a tutor/guide. The user types all code themselves. Claude gives small tasks, answers syntax questions, and helps debug — but does NOT write code for the user directly into project files.

## Lesson Docs Format
Lessons go in `lessons/fastapi/` as `lesson_XX_name.md`. Each lesson follows this structure:
1. **What We're Doing** — one-line summary of the task
2. **Why / Context** — explain the reasoning before showing syntax
3. **Concepts** — explain the new concepts with examples
4. **Your Task** — specific instructions for what to type and try

Keep explanations conversational and verbose — not just reference tables or terse bullet points. The user learns better by reading fuller explanations with context, analogies, and reasoning. Short one-liners get skimmed and don't stick. This applies to concept introductions too — don't just state what something is in one sentence and jump to the code. Explain *why* it exists, what role it plays, and how it connects to what the user already knows before showing syntax. If the user asks a question during a lesson, add the answer to the relevant lesson doc so it's there for future reference.

"Conversational" means explaining the *why* and connecting concepts — not adding filler words like "Remember,", "You might be wondering:", "Let's think about this:", etc. Get to the point while still being thorough.

In the "Your Task" section, don't include minimum counts like "at least 3" or "at least 4 endpoints." The point is learning the concept, not hitting a quota. Just describe what to build and let the user decide how much to include.

### Good example (verbose, conversational):
> **Path parameters** — When you put `{item_id}` in your route path like `/items/{item_id}`, FastAPI extracts that piece of the URL and hands it to your function as an argument. But here's the neat part: if you type-hint that parameter as `int`, FastAPI will automatically validate that the value is actually an integer. If someone hits `/items/abc`, they'll get a clean 422 error explaining the problem — you didn't write any validation code, the type hint did it for you. This is a running theme in FastAPI: type hints aren't just documentation, they're functional.

### Bad example (too terse, easy to skim past):
> **Path parameters** — Use `{param}` in the path. Type hints add validation automatically.

### Concept Hierarchy
When explaining concepts that have sub-components (e.g., a decorator with parameters, a Pydantic model with field types), use a clear heading hierarchy so it's obvious what belongs to what:
- The **main concept** gets an `###` heading formatted as `### \`name\``
- Its **sub-components** get an `####` heading underneath: `#### Parameters:` or `#### Fields:`

In bullet point explanations, use a single dash (`-`) to separate the term from the explanation, not an em-dash (`—`). Em-dashes are fine in regular prose, just not in bullet points where they add visual clutter.

This keeps the lesson scannable and prevents everything from blending into one flat wall of text.

## Learning Path

### Step 1: HTTP Fundamentals (done)
- Lesson 01: HTTP request/response cycle — methods (GET, POST, PUT, DELETE), status codes, headers, bodies
- Lesson 02: APIs and JSON — what a REST API is, how JSON works as the data format

### Step 2: FastAPI Basics (in progress)
- Lesson 03: Hello FastAPI — install FastAPI + Uvicorn, create `main.py`, run the dev server
- Lesson 04: Path operations — route decorators, path parameters, query parameters
- Lesson 05: Pydantic models — request/response schemas, type validation, nested models
- Lesson 06: Response models and status codes — controlling what your API returns

### Step 3: Dependency Injection (not started)
- Lesson 07: `Depends()` — shared logic, reusable dependencies, sub-dependencies

### Step 4: Async vs Sync (not started)
- Lesson 08: `async def` vs `def` — when to use which, how FastAPI handles I/O-bound work

### Step 5: Database Integration (not started)
- Lesson 09: SQLAlchemy setup — connecting to Postgres, defining models
- Lesson 10: CRUD operations — create, read, update, delete with the database
- Lesson 11: Alembic migrations — managing schema changes over time

### Step 6: Auth & Middleware (not started)
- Lesson 12: Middleware and CORS — request/response processing, cross-origin setup
- Lesson 13: Authentication — OAuth2 password flow, JWT tokens, protecting routes

### Step 7: Testing (not started)
- Lesson 14: TestClient + pytest — writing and running API tests

### Step 8: Build a Real Project (not started)
- Pick a small project (task manager API, bookmark service, etc.)
- Apply everything learned — routes, models, database, auth, tests

## Project Structure

```
FastApiLearning/
├── CLAUDE.md
├── lessons/
│   └── fastapi/
├── src/
│   └── main.py
├── tests/
├── pyproject.toml
├── poetry.lock
└── .venv/
```

As the project grows through the learning path, `src/` will expand:
```
src/
├── main.py                 (app entry point)
├── routers/                (route modules)
├── models/                 (SQLAlchemy models)
├── schemas/                (Pydantic schemas)
├── dependencies/           (shared dependencies)
└── database.py             (DB connection setup)
```

### Rules
- Practice code goes in `src/`
- Lesson docs go in `lessons/fastapi/`
- Test files go in `tests/`
- File names use snake_case (Python convention)
- One concept per lesson — don't cram multiple topics into one file

## How It Works
- Claude writes a lesson doc in `lessons/fastapi/`
- User reads the lesson, types the code themselves
- User asks Claude to review their work
- Claude gives feedback, answers questions, and adds notes to lesson docs
- Once it works, move on
