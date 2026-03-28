# Lesson 08: Project Structure

## What We're Doing
Splitting your growing `main.py` into organized files using `APIRouter` — so your project doesn't become an unreadable mess as you add more endpoints.

## Why / Context

Your `main.py` is already getting long. You've got card models, character models, blessing models, routes for cards, routes for characters, routes for Neow's blessings — all crammed into one file. Right now it's manageable, but imagine adding database logic, authentication, and more endpoints. One file would become hundreds of lines of unrelated code mixed together.

Every real FastAPI project splits things up. Models go in one place, routes go in another, and each "feature" (cards, characters, blessings) gets its own file. This isn't just about cleanliness — it's about being able to find things. When a bug report says "the card creation endpoint is broken," you want to open `routers/cards.py`, not scroll through a 500-line `main.py` trying to find the right function.

FastAPI gives you `APIRouter` for this — a way to define routes in separate files and plug them into your main app.

## Concepts

### `APIRouter` — Routes in Separate Files

`APIRouter` works exactly like the `app` object you've been using, but it's designed to be created in a separate file and then connected to the main app. You define routes on a router the same way you define them on `app`:

```python
# routers/cards.py
from fastapi import APIRouter, HTTPException, status

router = APIRouter()

@router.get("/cards")
def get_cards():
    return [{"name": "Strike"}, {"name": "Defend"}]

@router.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    return card
```

Notice: `@router.get` instead of `@app.get`. Everything else is the same — decorators, parameters, status codes, response models. You already know how to write these routes. The only difference is they live on a `router` instead of `app`.

Then in your `main.py`, you connect the router:

```python
# main.py
from fastapi import FastAPI
from routers.cards import router as cards_router

app = FastAPI()

app.include_router(cards_router)
```

`app.include_router()` takes all the routes from the router and adds them to the app. The app is still the central object — routers are just a way to organize routes across files before plugging them in.

**Try it:** Create a `src/routers/` folder with a `cards.py` file. Move your card-related routes into it using `APIRouter`. Import and include the router in `main.py`.

---

### `prefix` and `tags` — Organizing Your Router

When you include a router, you can add a **prefix** and **tags**:

```python
app.include_router(cards_router, prefix="/cards", tags=["Cards"])
```

- `prefix="/cards"` - automatically adds `/cards` to the beginning of every route in that router. So inside `cards.py`, you'd just write `@router.get("/")` instead of `@router.get("/cards")`, and `@router.get("/{card_id}")` instead of `@router.get("/cards/{card_id}")`. Less repetition.

- `tags=["Cards"]` - groups these endpoints together in the Swagger docs under a "Cards" heading. Without tags, all endpoints show up in one flat list. With tags, they're organized by feature. Note that `tags` must be a list, even if you're only passing one tag — `tags="Cards"` will error.

With prefixes, your router file becomes cleaner:

```python
# routers/cards.py
router = APIRouter()

@router.get("/")           # becomes /cards/
def get_cards():
    ...

@router.get("/{card_id}")  # becomes /cards/{card_id}
def get_card(card_id: str):
    ...

@router.post("/")          # becomes /cards/
def create_card(card: Card):
    ...
```

All the `/cards` repetition is gone — the prefix handles it. This makes the router file focused on what changes between routes (the specific path segments), not what's shared.

**Try it:** Add `prefix="/cards"` and `tags=["Cards"]` when including your cards router. Update the routes inside `cards.py` to remove the `/cards` prefix. Check Swagger — your endpoints should be grouped under a "Cards" tag.

---

### `Project Layout` — Where Everything Goes

Here's how to organize your project. You'll create folders for different concerns:

```
src/
├── main.py              (app creation, router includes)
├── routers/             (route definitions)
│   ├── __init__.py
│   ├── cards.py
│   ├── characters.py
│   └── neow.py
└── schemas/             (Pydantic models)
    ├── __init__.py
    ├── cards.py
    └── characters.py
```

The key idea: **separate by concern, not by type of code.**

- `routers/` - each file handles routes for one resource (cards, characters, blessings)
- `schemas/` - Pydantic models live here, separate from the route logic

`__init__.py` files make the folders into Python packages so you can import from them. They can be empty.

Your `main.py` becomes very short — just creating the app and including routers:

```python
from fastapi import FastAPI
from routers.cards import router as cards_router
from routers.characters import router as characters_router
from routers.neow import router as neow_router

app = FastAPI()

app.include_router(cards_router, prefix="/cards", tags=["Cards"])
app.include_router(characters_router, prefix="/characters", tags=["Characters"])
app.include_router(neow_router, prefix="/neow", tags=["Neow"])
```

That's it. Each router handles its own routes, the schemas are importable from anywhere, and `main.py` is just the entry point that ties everything together.

**Try it:** Create the full project structure above. Move your Pydantic models into `schemas/cards.py` and `schemas/characters.py`. Move your routes into the appropriate router files. Keep `main.py` clean — just app creation and router includes.

---

### `Imports Between Files` — How Everything Connects

Once you split things up, you need to import between files. This is where `__init__.py` and Python's module system come in.

From your router files, you'll import schemas:

```python
# routers/cards.py
from fastapi import APIRouter, HTTPException, status
from schemas.cards import Card, CardResponse, CardType

router = APIRouter()

@router.get("/", response_model=list[CardResponse])
def get_cards():
    ...
```

From `main.py`, you'll import routers:

```python
# main.py
from fastapi import FastAPI
from routers.cards import router as cards_router
```

The `as cards_router` part is important — every router file exports a variable called `router`, so you need to rename them on import to avoid conflicts.

If an import isn't working, check:
1. Does the folder have an `__init__.py` file?
2. Are you running Uvicorn from the `src/` directory or the project root? The import paths depend on where you run from.

**Try it:** After restructuring, run your server and make sure everything still works. Check Swagger — all your endpoints should still be there, now grouped by tags.

---

### `Shared Data` — Where Does the Hardcoded Data Go?

Right now you have a `cards` dictionary hardcoded in `main.py`. When you split into routers, that data needs to be accessible from the router file. For now, just put it at the top of the router file that uses it:

```python
# routers/cards.py
from fastapi import APIRouter

router = APIRouter()

cards = {
    "1": {"name": "Strike", "energy": 1, "card_type": "attack"},
    "2": {"name": "Defend", "energy": 1, "card_type": "skill"},
}

@router.get("/{card_id}")
def get_card(card_id: str):
    ...
```

This is temporary. When you get to the database lessons, this hardcoded data will be replaced with actual database queries. The router file won't store data at all — it'll just call the database.

---

## Your Task

This is a restructuring lesson — you're moving code, not writing new features.

1. Create `src/routers/` folder with `__init__.py`, `cards.py`, `characters.py`, and `neow.py`
2. Create `src/schemas/` folder with `__init__.py`, `cards.py`, and `characters.py`
3. Move your Pydantic models into the appropriate schema files
4. Move your routes into the appropriate router files using `APIRouter`
5. Update `main.py` to just create the app and include routers with prefixes and tags
6. Run the server and verify everything works — all endpoints should still function, now organized under tags in Swagger
7. Check that the Swagger docs show your endpoints grouped by tag (Cards, Characters, Neow)

When it's working, show me your project structure and I'll review it. Next lesson covers dependency injection.
