# Q21 Deep Dive: How `Depends()` Actually Works

## The Question

> What does `Depends()` do? Walk through what FastAPI does when it sees `Depends(some_function)` on a route parameter.

## The One-Line Answer

`Depends()` tells FastAPI: "Before running this route, call this function for me and give me the result."

## The Step-by-Step Flow

Let's use your actual code as the example:

```python
# src/dependencies/pagination.py
def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

# src/routers/cards.py
@router.get("/")
def get_cards(pagination: PaginationParams = Depends(pagination_params)):
    return cards[pagination.skip: pagination.skip + pagination.limit]
```

Here's what happens when a request hits `GET /cards?skip=5&limit=20`:

### 1. Startup: FastAPI inspects your route

When your app starts (not when a request comes in — at startup), FastAPI reads the signature of `get_cards` and sees:

```
pagination: PaginationParams = Depends(pagination_params)
```

It thinks: "OK, `pagination` is not a regular query parameter. It comes from calling `pagination_params`. Let me inspect *that* function too."

It reads the signature of `pagination_params` and sees:

```
skip: int = 0, limit: int = 10
```

FastAPI thinks: "These are plain parameters with type hints and defaults. They're not in any path string. So they must be query parameters. I'll extract them from the URL query string when a request comes in."

All of this happens once at startup. FastAPI builds a plan for how to handle each route before any request arrives.

### 2. Request arrives: FastAPI executes the plan

A request comes in: `GET /cards?skip=5&limit=20`

FastAPI follows the plan it built at startup:

1. Extract `skip=5` and `limit=20` from the query string.
2. Call `pagination_params(skip=5, limit=20)`.
3. Get the return value: `PaginationParams(skip=5, limit=20)`.
4. Pass that return value into `get_cards` as the `pagination` parameter.
5. Run `get_cards(pagination=PaginationParams(skip=5, limit=20))`.

Your route function never calls `pagination_params`. It never extracts `skip` and `limit` from the URL. FastAPI did all of that. Your route just receives the finished `PaginationParams` object and uses it.

### 3. What the client sees

From the client's perspective, they see `skip` and `limit` as query parameters in Swagger — even though those parameters aren't in your route function's signature. They're in the dependency's signature, but FastAPI surfaces them in the docs as if they were on the route itself. The client has no idea a dependency is involved.

## Why Not Just Put `skip` and `limit` on the Route Directly?

You could:

```python
@router.get("/")
def get_cards(skip: int = 0, limit: int = 10):
    return cards[skip: skip + limit]
```

This works. But now imagine you have 10 endpoints that all need pagination:

```python
@router.get("/cards")
def get_cards(skip: int = 0, limit: int = 10): ...

@router.get("/characters")
def get_characters(skip: int = 0, limit: int = 10): ...

@router.get("/blessings")
def get_blessings(skip: int = 0, limit: int = 10): ...
```

`skip: int = 0, limit: int = 10` is copy-pasted everywhere. Want to add a max limit of 100? Change it in 10 places. Want to rename `skip` to `offset`? 10 places. Want to add a `page` parameter? 10 places.

With a dependency, you change it once:

```python
def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    if limit > 100:
        limit = 100  # cap it
    return PaginationParams(skip=skip, limit=limit)
```

Every route that uses `Depends(pagination_params)` gets the fix automatically. That's the value.

## The `yield` Pattern (What You Remembered)

You mentioned the `yield` pattern in your quiz answer. That's a real thing — it's for dependencies that need **cleanup**. The most common example is a database session:

```python
def get_db():
    db = SessionLocal()    # open a database session
    try:
        yield db           # pause here — hand the session to the route
    finally:
        db.close()         # after the route finishes, close the session
```

Here's what happens:

1. FastAPI calls `get_db()`.
2. The function runs until `yield db`. It pauses and hands `db` to the route.
3. The route runs and does its database work using `db`.
4. After the route finishes (whether it succeeded or raised an error), FastAPI resumes `get_db()`.
5. The `finally` block runs `db.close()`, cleaning up the session.

This is like a context manager (`with` statement) but wired into FastAPI's dependency system. The `yield` is what makes it a "setup and teardown" dependency — everything before `yield` is setup, everything after is cleanup.

You'll use this exact pattern in Lesson 12-13 when you connect to the database. For now, just know that:
- **Regular dependencies** (with `return`) — FastAPI calls them, gets the result, passes it to your route. Done.
- **Yield dependencies** (with `yield`) — FastAPI calls them, they pause at `yield` to hand over a value, the route runs, then the dependency resumes for cleanup.

## How FastAPI Knows Where Parameters Come From

This is the part that confuses people. FastAPI uses the same logic for dependency function parameters as it does for route function parameters:

| Where the parameter name appears | What FastAPI treats it as |
|---|---|
| In the path string (`"/cards/{card_id}"`) | Path parameter |
| Not in the path, but is a Pydantic model | Request body |
| Not in the path, plain type with default | Query parameter (optional) |
| Not in the path, plain type without default | Query parameter (required) |
| Has `= Depends(...)` as default | Dependency — call the function and inject the result |

So when FastAPI sees `pagination_params(skip: int = 0, limit: int = 10)`, it applies these same rules: `skip` and `limit` aren't in any path string, they're plain types with defaults, so they're optional query parameters.

## TL;DR

- `Depends(some_function)` tells FastAPI to call `some_function` before your route runs and inject the return value.
- FastAPI inspects the dependency's signature to figure out what *it* needs (query params, path params, other dependencies).
- Your route never calls the dependency — FastAPI does it automatically.
- Regular dependencies use `return`. Dependencies with cleanup use `yield`.
- The value of `Depends()` is reusability: write the logic once, use it in many routes, change it in one place.
