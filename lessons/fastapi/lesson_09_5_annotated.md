# Lesson 09.5: `Annotated` from `typing`

## What We're Doing
Understanding what `Annotated` is, why it exists, and how FastAPI uses it — so the `Annotated[SomeType, Depends(...)]` pattern makes sense rather than just being something you copy-paste.

## Why / Context

You've now seen `Annotated` used in your dependencies. But it came from `typing` — Python's standard library — not from FastAPI. FastAPI didn't invent it, it just takes advantage of it. Understanding what `Annotated` actually does at the Python level makes everything else click.

The short version: `Annotated` lets you attach extra metadata to a type hint without changing what the type is. The type checker still sees the type. Other tools — like FastAPI — can read the metadata and act on it.

## Concepts

### `Type Hints Are Just Hints` — The Problem

Python type hints don't do anything at runtime by themselves. When you write:

```python
def greet(name: str) -> str:
    return f"Hello {name}"
```

The `: str` is purely informational. Python doesn't enforce it. If you pass an `int`, nothing breaks at runtime — the type hint is just there for your editor and type checker to read.

This is useful, but it means type hints are a one-way channel: you can say what type something is, but you can't attach any other information to it. If you want a tool to know something extra about a parameter — like "this value should come from a dependency" or "this field has a max length of 100" — there's nowhere in the type hint to put that information.

That's the gap `Annotated` fills.

---

### `Annotated` — Attaching Metadata to a Type

`Annotated` takes a type as its first argument and any number of metadata values after it:

```python
from typing import Annotated

Annotated[str, "some metadata"]
Annotated[int, "max value is 100"]
Annotated[str, some_object, "another piece of metadata"]
```

The first argument is the actual type. Everything after it is metadata. As far as Python's type checker is concerned, `Annotated[str, "some metadata"]` is just `str` — the metadata is ignored for type checking purposes. But other tools can inspect the metadata and do something with it.

This is the key insight: `Annotated` is a way to piggyback extra information onto a type hint, without breaking the type hint itself.

Note the square brackets `[]` — `Annotated` is a special typing form, not a regular function. You can't call it with parentheses like `Annotated(str, "metadata")`. That will throw a `TypeError: "<typing special form>" not callable`. Always use `[]`.

---

### `How FastAPI Uses It` — Depends as Metadata

FastAPI reads the metadata inside `Annotated` and acts on it. When it sees `Depends(some_function)` as metadata, it knows to run that function and inject the result:

```python
from typing import Annotated
from fastapi import Depends

def get_current_user():
    return {"id": 1, "name": "Lakhvir"}

UserDep = Annotated[dict, Depends(get_current_user)]

@router.get("/profile")
def get_profile(user: UserDep):
    return user
```

FastAPI inspects `UserDep`, sees `Annotated[dict, Depends(get_current_user)]`, and knows:
- The type is `dict` (for the type checker)
- There's a `Depends(get_current_user)` in the metadata (for FastAPI to run)

The type checker sees `user: dict`. FastAPI sees the dependency and calls `get_current_user()` before the route runs. Both get what they need from the same annotation.

This is why the old `= Depends(...)` pattern confused type checkers — it put the dependency in the default value position, which the type checker saw as a `Depends` object rather than a `dict`. `Annotated` puts the dependency in the metadata where the type checker ignores it, and FastAPI reads it.

---

### `Type Aliases` — Define Once, Use Everywhere

Because `Annotated[dict, Depends(get_current_user)]` is just a type, you can assign it to a variable and use that variable as a type hint anywhere:

```python
UserDep = Annotated[dict, Depends(get_current_user)]

@router.get("/profile")
def get_profile(user: UserDep):
    ...

@router.get("/settings")
def get_settings(user: UserDep):
    ...

@router.delete("/account")
def delete_account(user: UserDep):
    ...
```

Every route that needs the current user just uses `UserDep`. If `get_current_user` ever changes — say you swap it for a proper auth function — you update `UserDep` in one place and every route picks it up automatically. This is the whole point of the pattern.

---

### `Annotated` Beyond FastAPI

FastAPI isn't the only tool that uses `Annotated`. Pydantic uses it too, for attaching field constraints:

```python
from typing import Annotated
from pydantic import BaseModel, Field

class Card(BaseModel):
    name: Annotated[str, Field(max_length=100)]
    cost: Annotated[int, Field(ge=0, le=10)]
```

Here `Field(max_length=100)` is the metadata. Pydantic reads it and enforces the constraint. The type checker still sees `name: str` and `cost: int` — it doesn't care about the `Field` metadata.

The same mechanism, used by different tools for different purposes. Once you understand what `Annotated` does, you'll recognise it everywhere.

---

## Summary

- `Annotated[Type, metadata]` attaches extra information to a type hint without changing the type itself
- Type checkers see only the `Type` part — the metadata is invisible to them
- Other tools (FastAPI, Pydantic) inspect the metadata and act on it
- FastAPI uses `Depends(...)` as metadata to know which dependency to run
- Always use square brackets `[]`, never parentheses `()`
- Assigning `Annotated[...]` to a variable creates a reusable type alias — this is the pattern you use across your routes
