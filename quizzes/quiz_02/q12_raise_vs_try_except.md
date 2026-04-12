# Q12 Deep Dive: `raise` vs `try/except`

## The Confusion

You asked: "How would `raise` occur? Wouldn't it involve `try/except`? A little lost here."

You're mixing up two related but separate things in Python's exception system. They work together, but they're independent. You can use one without the other.

## `raise` vs `try/except`

- **`raise`** — *throws* an exception. It's how you say "something went wrong, stop normal execution right now."
- **`try/except`** — *catches* an exception. It's how you handle one that's already been thrown somewhere else.

Critically: **you can `raise` without any `try/except` nearby**. They don't have to appear together.

## Plain Python Example

```python
def divide(a, b):
    if b == 0:
        raise ValueError("Can't divide by zero")
    return a / b

result = divide(10, 0)
```

When you call `divide(10, 0)`:

1. The `if b == 0:` check is true.
2. The `raise ValueError(...)` line executes.
3. Python **immediately stops** executing the function. The `return a / b` line never runs.
4. Python walks back up the call stack looking for any code wrapped in `try/except` for `ValueError`.
5. If it finds one, that handler runs.
6. If it doesn't, the exception **bubbles up to the top** and crashes the program with a traceback.

So `raise` doesn't *need* a `try/except`. It just needs *somewhere* up the call stack to eventually catch it — otherwise the program crashes.

## How FastAPI Uses This

In a FastAPI route, you `raise HTTPException(...)` without writing any `try/except` yourself because **FastAPI catches it for you**. FastAPI wraps every route in a try/except internally. When your route raises an `HTTPException`, FastAPI's wrapper catches it and converts it into a proper HTTP response.

```python
@app.get("/cards/{card_id}")
def get_card(card_id: int):
    if card_id not in cards:
        raise HTTPException(status_code=404, detail="Card not found")
    return cards[card_id]
```

What happens when `card_id` doesn't exist:

1. Your code runs `raise HTTPException(...)`.
2. The function stops immediately. Nothing after the `raise` runs (notice there's no `else`).
3. The exception travels up the call stack.
4. FastAPI's internal wrapper (which called your route) catches it.
5. FastAPI sees it's an `HTTPException`, reads the `status_code` and `detail`, and builds an HTTP response.
6. The client receives `{"detail": "Card not found"}` with status 404.

You never write `try/except`. FastAPI handles the catching. Your job is just to `raise` when something is wrong, and FastAPI takes care of turning it into a proper HTTP response.

This is the same pattern you'd see if you imported a library — you don't have to wrap every call in try/except, you only do it when you actually want to handle an error locally.

## When Would You Actually Use `try/except` in a FastAPI Route?

Only when *you* want to handle an exception locally before deciding what to do with it. The most common case: you call a third-party library that throws its own exceptions, and you want to convert those into clean `HTTPException`s for your API consumers.

```python
@app.get("/external")
def fetch_external():
    try:
        data = some_third_party_library.fetch()
    except SomeWeirdError as exc:
        raise HTTPException(
            status_code=503,
            detail="External service unavailable"
        )
    return data
```

Here you're catching one exception type (`SomeWeirdError`) and re-raising as a different one (`HTTPException`). The reason: `SomeWeirdError` would just become a generic 500 if you let it bubble up, but a 503 with a clean message is more useful for the client.

### What's `as exc`?

The `as exc` part gives you a reference to the actual exception object so you can inspect it or log it. It's not a keyword — `exc` is just a variable name. You could call it `e`, `err`, or anything else. The convention is `exc` or `e`.

This matters because in production, you want to **log the real error for your team** while **sending a clean message to the client**:

```python
except SomeWeirdError as exc:
    # exc is the exception object — has attributes like exc.args, str(exc), etc.
    logger.error(f"External API failed: {exc}")   # your team sees the real error in logs
    raise HTTPException(status_code=503, detail="Service unavailable")  # client sees a clean message
```

The client gets `{"detail": "Service unavailable"}` with a 503 status — no internal details leaked. Your logs show `"External API failed: connection refused to api.example.com"` — the actual error your team needs to debug. Two audiences, two different messages, from the same `except` block.

Without `as exc`, you can still catch and re-raise, but you lose access to the original error details. You'd be logging blind.

Outside of this pattern, you almost never need `try/except` in a FastAPI route. If your code can fail in a way you can predict, just `raise HTTPException` directly.

## The Fix to Your Q12 Answer

Your original code was almost right. You just needed the `raise` keyword in front of `HTTPException(...)`:

```python
from fastapi import FastAPI, HTTPException, status

app = FastAPI()

@app.get("/cards/{card_id}")
def get_card(card_id: int):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Card not found"
    )
```

The `raise` keyword is what actually triggers the exception. Without it, you'd just be creating an `HTTPException` object and immediately throwing it away — like writing `5 + 5` on a line by itself. The math happens, but the result has nowhere to go.

This is one of those quirks of Python: instantiating an exception class doesn't do anything special by itself. Only `raise` makes it actually behave like an error.

```python
HTTPException(status_code=404, detail="...")        # creates the object, does nothing
raise HTTPException(status_code=404, detail="...")  # actually triggers the error
```

## TL;DR

- `raise` throws an exception. `try/except` catches one. They're independent.
- You can `raise` without writing any `try/except` — the exception just travels up the stack until *something* catches it.
- In FastAPI, **FastAPI itself catches your `HTTPException`**. You don't write try/except in your routes.
- Use `try/except` in routes only when you need to convert a third-party library's exceptions into clean `HTTPException`s.
- Don't forget the `raise` keyword — `HTTPException(...)` by itself does nothing.
