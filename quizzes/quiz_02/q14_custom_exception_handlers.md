# Q14 Deep Dive: Custom Exception Handlers

## The Question

> Why would you write a custom exception handler instead of just raising `HTTPException` everywhere?

## The Problem with `HTTPException` Everywhere

`HTTPException` works fine when you have a handful of routes. But as your API grows, a pattern emerges:

```python
@router.get("/cards/{card_id}")
def get_card(card_id: int):
    card = find_card(card_id)
    if not card:
        raise HTTPException(
            status_code=404,
            detail={"code": "CARD_NOT_FOUND", "message": f"Card {card_id} not found"}
        )
    return card

@router.get("/characters/{character_id}")
def get_character(character_id: int):
    character = find_character(character_id)
    if not character:
        raise HTTPException(
            status_code=404,
            detail={"code": "CHARACTER_NOT_FOUND", "message": f"Character {character_id} not found"}
        )
    return character

@router.get("/blessings/{blessing_id}")
def get_blessing(blessing_id: int):
    blessing = find_blessing(blessing_id)
    if not blessing:
        raise HTTPException(
            status_code=404,
            detail={"code": "BLESSING_NOT_FOUND", "message": f"Blessing {blessing_id} not found"}
        )
    return blessing
```

Three routes, three `HTTPException` blocks, all doing the same thing with slightly different values. Now imagine 30 routes. Now imagine your frontend team asks you to add a `trace_id` field to every error response for debugging. You'd have to update every single `raise HTTPException(...)` across your entire codebase.

This is the problem: **`HTTPException` scatters your error formatting logic across every route.**

## The Solution: Custom Exceptions + Global Handlers

Instead of formatting the error at every raise site, you split the work into two parts:

1. **A custom exception class** — just carries the data (what went wrong)
2. **A global exception handler** — decides how to format the response (what the client sees)

### Step 1: Define your custom exception

```python
# src/exceptions.py
class NotFoundError(Exception):
    def __init__(self, resource: str, resource_id: int | str):
        self.resource = resource
        self.resource_id = resource_id
```

This is just a plain Python class that inherits from `Exception`. It's not an `HTTPException` — it doesn't know about status codes or HTTP at all. It just holds the data: what resource, what ID.

### Step 2: Register a global handler

```python
# src/main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.exceptions import NotFoundError

app = FastAPI()

@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "code": f"{exc.resource.upper()}_NOT_FOUND",
            "message": f"{exc.resource} {exc.resource_id} not found",
        }
    )
```

`@app.exception_handler(NotFoundError)` tells FastAPI: "Whenever a `NotFoundError` is raised anywhere in my app — in any route, any dependency, any service function — catch it and run this function instead of returning a generic 500."

The handler receives the exception object (`exc`) and builds the response. All the formatting logic lives here, in one place.

### Step 3: Raise the clean exception in your routes

```python
@router.get("/cards/{card_id}")
def get_card(card_id: int):
    card = find_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    return card

@router.get("/characters/{character_id}")
def get_character(character_id: int):
    character = find_character(character_id)
    if not character:
        raise NotFoundError("Character", character_id)
    return character

@router.get("/blessings/{blessing_id}")
def get_blessing(blessing_id: int):
    blessing = find_blessing(blessing_id)
    if not blessing:
        raise NotFoundError("Blessing", blessing_id)
    return blessing
```

Compare this to the `HTTPException` version. Each route is one line instead of five. The routes don't know or care about status codes, JSON structure, or error formatting. They just say "this thing wasn't found" and the handler takes care of the rest.

## Why This Matters

### 1. Single source of truth for error format

Want to add a `trace_id` to every error? Change the handler once:

```python
@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError):
    return JSONResponse(
        status_code=404,
        content={
            "code": f"{exc.resource.upper()}_NOT_FOUND",
            "message": f"{exc.resource} {exc.resource_id} not found",
            "trace_id": request.headers.get("X-Trace-ID", "none"),
        }
    )
```

Every 404 in your entire API now includes `trace_id`. You touched one function, not 30 routes.

### 2. Separation of concerns

Your route functions describe the **business logic** — what the endpoint does. The exception handler describes the **error presentation** — what the client sees. These are two different responsibilities, and mixing them makes both harder to change.

### 3. Catches errors from anywhere

`HTTPException` only works when you explicitly raise it. But what if an error happens deep inside a service function that your route calls?

```python
# src/services/cards.py
def find_card(card_id: int):
    card = db.query(Card).get(card_id)
    if not card:
        raise NotFoundError("Card", card_id)  # works!
    return card
```

The service function doesn't import `HTTPException` — it doesn't even know it's running inside a web app. It just raises a clean Python exception. The global handler, registered on the app, catches it no matter how deep in the call stack it was raised.

With `HTTPException`, you'd have to either raise it in the service (which couples your business logic to FastAPI) or catch `NotFoundError` in the route and re-raise as `HTTPException` (which is extra boilerplate).

### 4. Multiple exception types

You can register handlers for different exception types:

```python
class NotFoundError(Exception): ...
class ConflictError(Exception): ...
class ForbiddenError(Exception): ...

@app.exception_handler(NotFoundError)
def handle_not_found(request, exc):
    return JSONResponse(status_code=404, content={...})

@app.exception_handler(ConflictError)
def handle_conflict(request, exc):
    return JSONResponse(status_code=409, content={...})

@app.exception_handler(ForbiddenError)
def handle_forbidden(request, exc):
    return JSONResponse(status_code=403, content={...})
```

Each error type gets its own handler with its own status code and format. Your routes just raise the right exception type — they never think about HTTP.

## When to Use Which

**Use `HTTPException` when:**
- You have a small app with few routes
- The error is a one-off case specific to that route
- You're prototyping and don't want the ceremony of custom exceptions

**Use custom exception handlers when:**
- Your API has many routes that share common error patterns
- You want consistent error formatting across the entire API
- Your business logic (services, utilities) needs to raise errors without knowing about HTTP
- Your frontend team needs a specific, reliable error shape they can parse

For this project right now, `HTTPException` is fine — you don't have enough routes to feel the pain. But in a production codebase with 50+ endpoints, custom exception handlers are standard practice.

## How It Connects to What You Already Know

Remember how `raise` works from the Q12 doc: you raise an exception, it bubbles up the call stack, and something catches it. With `HTTPException`, FastAPI's built-in handler catches it. With custom exceptions, **your** handler catches it because you registered it with `@app.exception_handler(...)`.

Same mechanism, just with your own exception types and your own formatting logic.

## TL;DR

- `HTTPException` everywhere = error formatting scattered across every route. Works for small apps.
- Custom exception handlers = error formatting in one place. Routes just raise clean exceptions. Scales to large apps.
- Register handlers with `@app.exception_handler(YourExceptionClass)`.
- Custom exceptions don't know about HTTP — they just carry data. The handler decides the status code and response format.
- This pattern separates business logic (what went wrong) from error presentation (what the client sees).
