# Lesson 07: Error Handling

## What We're Doing
Learning how to handle errors in your API — returning meaningful error responses when things go wrong instead of letting your app crash or return confusing messages.

## Why / Context

So far, the only errors your API returns are the automatic 422 validation errors from Pydantic. Those are great, but they only cover one case: bad input data. What about when someone requests a card that doesn't exist? Or tries to delete something they don't have permission to? Or your code hits an unexpected bug?

Without proper error handling, your API either crashes with a 500 error (giving the client no useful information) or silently returns wrong data. Neither is acceptable. A well-designed API tells the client exactly what went wrong, in a consistent format, with the right status code.

FastAPI gives you `HTTPException` for this — a way to stop a request and send back a specific error response. It's the most common tool you'll use for error handling, and you'll use it in almost every endpoint once you have real data.

## Concepts

### `HTTPException` — Raising Errors on Purpose

`HTTPException` is a special exception you raise when something goes wrong. It immediately stops your function and sends an error response to the client with the status code and message you specify.

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

cards = {"1": {"name": "Strike", "energy": 1, "card_type": "attack"}}

@app.get("/cards/{card_id}")
def get_card(card_id: str):
    if card_id not in cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return cards[card_id]
```

If someone hits `/cards/999`, they get:

```json
{
    "detail": "Card not found"
}
```

With a `404 Not Found` status code. Without the `HTTPException`, your code would either return `None` (confusing) or crash with a KeyError (ugly 500 error).

The `detail` parameter is what the client sees in the response body. It can be a string, a dict, or even a list — whatever helps the client understand what went wrong.

**Try it:** Add a hardcoded dictionary of cards to your `main.py` (just a few entries). Update your `GET /cards/{card_id}` endpoint to look up the card and raise a 404 if it doesn't exist.

---

### `Common Error Patterns` — When to Use Which Status Code

Different situations call for different error codes. Here are the ones you'll use most:

**404 Not Found** — the resource doesn't exist.

```python
@app.get("/cards/{card_id}")
def get_card(card_id: str):
    if card_id not in cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return cards[card_id]
```

**400 Bad Request** — the request doesn't make sense, but it's not a validation issue (Pydantic handles those with 422). Use this for business logic violations.

```python
@app.post("/decks/{character_name}/cards")
def add_card_to_deck(character_name: str, card: Card):
    if len(deck) >= 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deck is full — maximum 50 cards"
        )
    # add card logic
```

**409 Conflict** — the request conflicts with the current state. Like trying to create something that already exists.

```python
@app.post("/cards")
def create_card(card: Card):
    if card.name in existing_cards:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Card '{card.name}' already exists"
        )
    # create logic
```

The pattern is always the same: check a condition, raise `HTTPException` if it fails, continue if it passes. Your endpoint's "happy path" code stays clean because the errors are handled early and explicitly.

**Try it:** Add a 409 check to your `POST /cards` endpoint — if a card with the same name already exists in your hardcoded dictionary, return a conflict error. Test it by submitting the same card twice.

---

### `detail` — Making Error Messages Useful

The `detail` field can be more than just a string. You can pass structured data to give the client more context:

```python
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail={
        "message": "Card not found",
        "card_id": card_id,
        "suggestion": "Use GET /cards to see available cards"
    }
)
```

The response body would be:

```json
{
    "detail": {
        "message": "Card not found",
        "card_id": "999",
        "suggestion": "Use GET /cards to see available cards"
    }
}
```

In practice, most APIs stick with simple string messages. But knowing you can pass structured data is useful when debugging — sometimes the client needs more than just "not found" to figure out what went wrong.

**Try it:** Update one of your error responses to use a dictionary instead of a plain string. See how it looks in Swagger.

---

### `Custom Headers on Errors` — Rarely Needed, Good to Know

You can attach custom headers to error responses. This is uncommon but occasionally useful — for example, telling the client how long to wait before retrying.

```python
raise HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail="Too many requests — slow down",
    headers={"Retry-After": "30"}
)
```

The `Retry-After` header tells the client "wait 30 seconds before trying again." You probably won't use this often, but it's there when you need it.

---

### `Consistent Error Responses` — Why It Matters

Every error from your API should follow the same format. If one endpoint returns `{"detail": "not found"}` and another returns `{"error": "missing", "code": 404}`, the client has to handle each one differently. That's a nightmare.

FastAPI's `HTTPException` already gives you consistency — every error comes back as `{"detail": "..."}`. Stick with this format. When you get to building the Gator Days project, every error your API returns will have the same shape, making it easy for your httpx scraper to handle failures.

As your API grows, you'll notice a problem: every route that can fail has its own `raise HTTPException(...)` with its own status code and message format. If you have 30 routes and your frontend team asks you to add a `trace_id` field to every error, you'd have to update 30 raise statements. That's where **custom exception handlers** come in.

The idea: instead of formatting the error at every raise site, you split the work into two parts — a custom exception class that carries the data, and a global handler that formats the response.

#### Step 1: Define a custom exception

```python
# src/exceptions.py
class NotFoundError(Exception):
    def __init__(self, resource: str, resource_id: int | str):
        self.resource = resource
        self.resource_id = resource_id
```

This is a plain Python class. It doesn't know about HTTP — it just holds what went wrong.

#### Step 2: Register a global handler

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

`@app.exception_handler(NotFoundError)` tells FastAPI: "Whenever a `NotFoundError` is raised anywhere in my app — any route, any dependency, any service function — catch it and run this function." All error formatting lives here, in one place.

#### Step 3: Raise in your routes

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
```

Compare this to the `HTTPException` version — each route is one line instead of five. The routes don't know about status codes or JSON structure. They just say "this thing wasn't found" and the handler takes care of the rest.

#### Why this matters in production

- **One place to change.** Want to add `trace_id` to every error? Change the handler once, not 30 routes.
- **Works from anywhere.** A service function deep in your codebase can `raise NotFoundError(...)` without importing anything from FastAPI. The handler catches it no matter how deep in the call stack.
- **Multiple exception types.** You can register handlers for `NotFoundError` (404), `ConflictError` (409), `ForbiddenError` (403), etc. Each gets its own handler, status code, and format.
- **Separation of concerns.** Routes handle business logic. Handlers handle error presentation. Two different jobs, two different places.

#### When to use which

`HTTPException` is fine for small APIs and one-off errors. Custom exception handlers are the standard in production codebases with many endpoints that need consistent error formatting. You don't need to implement this right now — but you will use this pattern when the codebase grows, especially once you have database operations that can fail in predictable ways.

**Try it:** Create a `src/exceptions.py` file with a `NotFoundError` class. Register a handler for it in `main.py`. Update one of your routes to raise `NotFoundError` instead of `HTTPException`. Test it in Swagger and confirm the response format matches what your handler returns.

---

### `Don't Catch Everything` — Let FastAPI Handle What It Can

A common mistake is wrapping everything in try/except blocks. FastAPI already handles a lot of errors for you:

- **Pydantic validation errors** → automatic 422 with detailed messages
- **Unhandled exceptions** → automatic 500 Internal Server Error
- **Wrong HTTP method** → automatic 405 Method Not Allowed

You only need `HTTPException` for **business logic errors** — things FastAPI can't know about. "Card not found" is business logic. "Invalid JSON" is not — FastAPI already handles that.

```python
# DON'T do this — FastAPI already handles validation
@app.post("/cards")
def create_card(card: Card):
    try:
        # Pydantic already validated this
        if not isinstance(card.name, str):
            raise HTTPException(...)
    except:
        raise HTTPException(...)

# DO this — only check business logic
@app.post("/cards")
def create_card(card: Card):
    if card.name in existing_cards:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Card '{card.name}' already exists"
        )
    # create logic
```

**Try it:** Try sending a request with the wrong HTTP method — like a POST to an endpoint that only accepts GET. See what FastAPI returns automatically without you writing any error handling.

---

## Your Task

Here's the full checklist:

1. Added a hardcoded dictionary of cards to work with
2. `GET /cards/{card_id}` raises 404 if the card doesn't exist
3. `POST /cards` raises 409 if a card with that name already exists
4. At least one error response uses a dictionary for `detail` instead of a plain string
5. Tested all error cases in Swagger — verified the status codes and response bodies
6. Tested sending a wrong HTTP method to see FastAPI's automatic error handling

When it's working, show me your code. Next lesson covers project structure — splitting your growing `main.py` into organized files.
