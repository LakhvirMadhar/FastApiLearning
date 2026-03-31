# Lesson 09: Dependency Injection with `Depends()`

## What We're Doing
Using FastAPI's `Depends()` to share common logic across route functions — so you stop repeating yourself.

## Why / Context

Look at your current routes. Imagine you add authentication later — every route needs to check if the user is logged in. Or imagine you add pagination — every list endpoint needs `skip` and `limit` parameters. Without dependency injection, you'd copy-paste the same code into every route function. When the logic changes, you'd have to update it in ten places.

Dependency injection is FastAPI's answer to this. You write a function once, and FastAPI automatically calls it and passes the result to any route that needs it. The route doesn't call the function itself — it just declares "I depend on this" and FastAPI handles the rest. That's the "injection" part: FastAPI injects the result into your function.

This pattern is one of the things that makes FastAPI different from Flask. Flask makes you do this manually (decorators, `g` object, etc.). FastAPI builds it into the framework.

## Concepts

### `Depends()` — The Basics

A dependency is just a regular Python function. There's nothing special about it — no decorator, no base class. It becomes a dependency when you use it inside `Depends()` as a default value for a route parameter.

Here's a simple example. Say multiple routes need the same pagination parameters:

```python
# Without dependencies — repeated in every route
@router.get("/cards")
def get_cards(skip: int = 0, limit: int = 10):
    return cards[skip: skip + limit]

@router.get("/characters")
def get_characters(skip: int = 0, limit: int = 10):
    return characters[skip: skip + limit]
```

`skip` and `limit` are duplicated. Now imagine you want to add a maximum limit of 100, or rename `skip` to `offset`. You'd have to change every route.

With a dependency:

```python
from fastapi import Depends

def pagination_params(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@router.get("/cards")
def get_cards(pagination: dict = Depends(pagination_params)):
    return cards[pagination["skip"]: pagination["skip"] + pagination["limit"]]
```

FastAPI sees `Depends(pagination_params)` and does the following automatically:
1. Looks at `pagination_params` and sees it expects `skip` and `limit` from the query string
2. Extracts those values from the incoming request
3. Calls `pagination_params(skip=..., limit=...)`
4. Passes the return value into `get_cards` as the `pagination` parameter

The route itself never calls `pagination_params()` — FastAPI does that for you. The route just receives the result.

**Try it:** Create a `pagination_params` function and use it in your `get_cards` route with `Depends()`. Test it in Swagger — you should still see `skip` and `limit` as query parameters, even though they're defined in the dependency function, not in the route.

---

### `Returning Objects` — Using Pydantic Models in Dependencies

Returning a dict from a dependency works, but accessing values with `pagination["skip"]` isn't great. You can return a Pydantic model instead for cleaner access:

```python
from pydantic import BaseModel

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 10

def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

@router.get("/cards")
def get_cards(pagination: PaginationParams = Depends(pagination_params)):
    return cards[pagination.skip: pagination.skip + pagination.limit]
```

Now it's `pagination.skip` instead of `pagination["skip"]` — cleaner, type-safe, and your editor gives you autocomplete.

**Try it:** Create a `PaginationParams` schema and update your dependency to return it. Verify Swagger still works the same way.

---

### `Where Dependencies Live` — File Organization

Dependencies get their own folder: `src/dependencies/`. Each file holds related dependencies:

```
src/
├── dependencies/
│   ├── __init__.py
│   └── pagination.py
```

Then import them in your router files:

```python
from src.dependencies.pagination import pagination_params
```

This follows the same pattern as schemas and routers — each concern gets its own place.

**Try it:** Create `src/dependencies/pagination.py`, move your pagination dependency there, and import it in your router.

---

### `Router-Level Dependencies` — Apply to All Routes

Instead of adding `Depends()` to each route individually, you can apply a dependency to every route in a router:

```python
router = APIRouter(dependencies=[Depends(some_dependency)])
```

Every route on that router will run `some_dependency` before executing. This is useful for things like authentication — instead of adding `Depends(verify_token)` to 15 routes, you put it on the router once.

The difference: with router-level dependencies, the return value isn't injected into the route function. The dependency runs (and can raise exceptions to block the request), but the route doesn't receive its return value. This makes sense for "gatekeeper" dependencies like auth checks — the route doesn't need the return value, it just needs the check to pass.

If a route *does* need the return value (like pagination), keep it as a parameter-level dependency with `Depends()` in the function signature.

**Try it:** Create a simple logging dependency that prints the current time when a request comes in. Apply it at the router level so every route in your cards router logs the request time. Check your terminal output when you hit different endpoints.

---

### `Sub-Dependencies` — Dependencies That Depend on Other Dependencies

Dependencies can depend on other dependencies. FastAPI resolves the entire chain automatically.

```python
def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

def validated_pagination(pagination: PaginationParams = Depends(pagination_params)) -> PaginationParams:
    if pagination.limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit cannot exceed 100"
        )
    return pagination

@router.get("/cards")
def get_cards(pagination: PaginationParams = Depends(validated_pagination)):
    ...
```

When a request hits `get_cards`:
1. FastAPI sees `Depends(validated_pagination)`
2. Looks at `validated_pagination` and sees it depends on `Depends(pagination_params)`
3. Calls `pagination_params` first, gets the result
4. Passes that result into `validated_pagination`
5. Passes *that* result into `get_cards`

The chain can go as deep as you need. FastAPI figures out the order and calls everything in the right sequence. This is how real applications compose complex behavior from small, reusable pieces — authentication checks that depend on token parsing, which depends on header extraction, etc.

**Try it:** Create a `validated_pagination` dependency that wraps `pagination_params` and raises an `HTTPException` if `limit` is over 100. Use it in a route and test with `?limit=200` in Swagger to see the error.

---

## Your Task

1. Create `src/dependencies/` folder with `__init__.py` and `pagination.py`
2. Write a `PaginationParams` schema (or put it in your existing schemas)
3. Write a `pagination_params` dependency function that returns `PaginationParams`
4. Write a `validated_pagination` sub-dependency that caps `limit` at 100
5. Use the dependency in your `get_cards` route
6. Create a simple logging dependency and apply it at the router level on your cards router
7. Run the server — test pagination in Swagger, try `?limit=200` to see the validation error, and check your terminal for the log output
