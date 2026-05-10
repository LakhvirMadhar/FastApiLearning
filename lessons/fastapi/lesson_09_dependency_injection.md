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
```

Now it's `pagination.skip` instead of `pagination["skip"]` — cleaner, type-safe, and your editor gives you autocomplete.

**Try it:** Create a `PaginationParams` schema and update your dependency to return it.

---

### `Annotated` — The Modern Way to Write Dependencies

The `= Depends(...)` default value pattern works, but it has a flaw: type checkers like mypy and pyright get confused. The parameter looks like it has a default value of a `Depends` object, but at runtime it's actually the return value of your dependency function. Type checkers see the mismatch and either complain or need suppression comments (`# type: ignore`) to stay quiet. You've probably seen this at work — people sprinkling `# type: ignore` on route parameters.

The fix is `Annotated` from the `typing` module. Instead of putting `Depends()` as a default value, you attach it to the type hint itself:

```python
from typing import Annotated
from fastapi import Depends

PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]

@router.get("/cards")
def get_cards(pagination: PaginationDep):
    return cards[pagination.skip: pagination.skip + pagination.limit]
```

FastAPI recognizes `Annotated[SomeType, Depends(...)]` and handles it the same way — the dependency still runs, the result still gets injected. But now the type checker sees `pagination: PaginationParams` (effectively), which is correct, and the suppression comments go away. Note that `Annotated` uses square brackets `[]`, not parentheses `()` — it's a special typing form, not a regular function call.

The aliases belong in a central `dependencies.py` file. The individual files (`pagination.py`, `database.py`, etc.) define the dependency functions, and `dependencies.py` imports them and defines all the `Annotated` aliases in one place:

```python
# src/dependencies/pagination.py
def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)
```

```python
# src/dependencies.py
from typing import Annotated
from fastapi import Depends
from src.dependencies.pagination import pagination_params
from src.schemas.pagination import PaginationParams

PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]
# SessionDep, AuthDep, etc. all go here too as the project grows
```

```python
# src/routers/cards.py
from src.dependencies import PaginationDep

@router.get("/cards")
def get_cards(pagination: PaginationDep):
    ...
```

Every router imports from `src.dependencies` — one consistent source. If a dependency function moves, is renamed, or gets swapped out, you update `dependencies.py` and nothing else breaks. Without this, you'd have `Depends(pagination_params)` scattered across every router file and no single place to change it.

This is the pattern the FastAPI docs now recommend for all dependencies.

**Try it:** Define `PaginationDep` in your `pagination.py` file and update your route to use it as a plain type hint.

---

### `Where Dependencies Live` — File Organization

Dependencies get their own folder: `src/dependencies/`. Each file holds related dependencies and their `Annotated` aliases:

```
src/
├── dependencies/
│   ├── __init__.py
│   └── pagination.py
```

Then import the alias in your router files:

```python
from src.dependencies.pagination import PaginationDep
```

This follows the same pattern as schemas and routers — each concern gets its own place.

**Try it:** Create `src/dependencies/pagination.py`, move your pagination dependency and `PaginationDep` alias there, and import it in your router.

---

### `Router-Level Dependencies` — Apply to All Routes

Instead of adding `Depends()` to each route individually, you can apply a dependency to every route in a router:

```python
router = APIRouter(dependencies=[Depends(some_dependency)])
```

Every route on that router will run `some_dependency` before executing. This is useful for things like authentication — instead of adding `Depends(verify_token)` to 15 routes, you put it on the router once.

This is where it helps to have a clear mental model of the two different jobs `Depends()` can do:

**Dependency as injection** — you need the return value inside your function. FastAPI runs the dependency and hands its return value to your route as a named parameter:

```python
def get_cards(db: SessionDep):
    cards = db.query(Card).all()  # db is the Session returned by get_db
```

**Dependency as a gate/side effect** — you just need it to run, you don't care what it returns. FastAPI runs it before the route, but injects nothing:

```python
router = APIRouter(dependencies=[Depends(verify_token)])
# verify_token raises 401 if the token is bad, otherwise does nothing
# the route never receives any value from it
```

The mental model: function parameter `Depends()` means "give me this value." `dependencies=[]` means "run this — I don't need what it returns."

This is why `Annotated` aliases don't make sense for `dependencies=[]` — `Annotated` is for attaching dependency metadata to a type so FastAPI knows what value to inject into a parameter. When there's no parameter to inject into, there's nothing for `Annotated` to attach to.

The real-world version of router-level dependencies is auth. You write a dependency that checks a JWT token and raises a 401 if it's invalid. Every route on that router is protected without adding anything to the individual function signatures.

**Try it:** Create a simple logging dependency that prints the current time when a request comes in. Apply it at the router level so every route in your cards router logs the request time. Check your terminal output when you hit different endpoints.

---

### `Sub-Dependencies` — Dependencies That Depend on Other Dependencies

Dependencies can depend on other dependencies. FastAPI resolves the entire chain automatically.

```python
# src/dependencies/pagination.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 10

def pagination_params(skip: int = 0, limit: int = 10) -> PaginationParams:
    return PaginationParams(skip=skip, limit=limit)

PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]

def validated_pagination(pagination: PaginationDep) -> PaginationParams:
    if pagination.limit > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit cannot exceed 100"
        )
    return pagination

ValidatedPaginationDep = Annotated[PaginationParams, Depends(validated_pagination)]
```

```python
# src/routers/cards.py
from src.dependencies.pagination import ValidatedPaginationDep

@router.get("/cards")
def get_cards(pagination: ValidatedPaginationDep):
    ...
```

When a request hits `get_cards`:
1. FastAPI sees `ValidatedPaginationDep` and resolves `Depends(validated_pagination)`
2. Looks at `validated_pagination` and sees it depends on `PaginationDep`, which resolves `Depends(pagination_params)`
3. Calls `pagination_params` first, gets the result
4. Passes that result into `validated_pagination`
5. Passes *that* result into `get_cards`

The chain can go as deep as you need. FastAPI figures out the order and calls everything in the right sequence. This is how real applications compose complex behavior from small, reusable pieces — authentication checks that depend on token parsing, which depends on header extraction, etc.

**Try it:** Create a `validated_pagination` dependency that wraps `PaginationDep` and raises an `HTTPException` if `limit` is over 100. Define `ValidatedPaginationDep` and use it in a route. Test with `?limit=200` in Swagger to see the error.

---

---

### The Four Variations — Summary

The core idea is simple: **a dependency is a function FastAPI calls for you before your route runs.** Everything else is just answering "what do you do with what it returns?" and "where do you attach it?":

1. **Inject the return value into a route** — `db: SessionDep`, `pagination: ValidatedPaginationDep`. You need what the dependency returns, so it goes in the function signature.

2. **Side effect only, no return value** — `dependencies=[Depends(verify_token)]` on a router or route. You just need it to run — to check something, log something, block the request. The return value is discarded.

3. **Sub-dependencies** — a dependency that depends on another dependency. `validated_pagination` depends on `pagination_params`. FastAPI resolves the whole chain automatically in the right order.

4. **Router-level vs route-level** — you can apply a dependency to one specific route, or to every route on a router at once.

1 and 2 are the fundamental split. 3 and 4 are just "how deep can it go" and "where do you attach it." If you go back to the core idea whenever something feels confusing, the variation you're looking at will follow logically.

---

## Your Task

1. Create `src/dependencies/` folder with `__init__.py` and `pagination.py`
2. Write a `PaginationParams` schema (or put it in your existing schemas)
3. Write a `pagination_params` dependency function that returns `PaginationParams`
4. Define `PaginationDep = Annotated[PaginationParams, Depends(pagination_params)]`
5. Write a `validated_pagination` sub-dependency that uses `PaginationDep` and caps `limit` at 100
6. Define `ValidatedPaginationDep = Annotated[PaginationParams, Depends(validated_pagination)]`
7. Use `ValidatedPaginationDep` in your `get_cards` route as a plain type hint
8. Create a simple logging dependency and apply it at the router level on your cards router
9. Run the server — test pagination in Swagger, try `?limit=200` to see the validation error, and check your terminal for the log output
