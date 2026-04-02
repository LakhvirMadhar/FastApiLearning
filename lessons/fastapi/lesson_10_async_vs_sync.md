# Lesson 10: `async def` vs `def`

## What We're Doing
Understanding when to use `async def` vs `def` for your route functions — and how FastAPI handles each one differently behind the scenes.

## Why / Context

Every route function you've written so far uses `def`. That works fine. But you'll see a lot of FastAPI code using `async def` instead, and at some point you'll need to make external HTTP calls, talk to a database, or read files — all of which are I/O-bound operations that can benefit from async.

The problem is, most tutorials just say "use `async def` for async stuff" without explaining what that actually means or what happens when you pick the wrong one. This lesson covers the mechanics so you can make an informed choice instead of guessing.

## Concepts

### `def` vs `async def` — What FastAPI Does With Each

When FastAPI sees a regular `def` route:

```python
@router.get("/cards")
def get_cards():
    return [{"name": "Strike"}]
```

It runs that function in a **thread pool**. FastAPI knows that a regular `def` *might* do something blocking (like a database query or file read), so it runs it in a separate thread to avoid freezing the entire server. This means other requests can still be handled while your function is doing its work.

When FastAPI sees an `async def` route:

```python
@router.get("/cards")
async def get_cards():
    return [{"name": "Strike"}]
```

It runs that function on the **main async event loop**. This is faster (no thread overhead), but there's a catch: if you do anything blocking inside an `async def` function — like a regular database call or `time.sleep()` — you freeze the entire event loop. No other requests get processed until your blocking operation finishes.

So the rule is straightforward:

- **`def`** — use when your function does blocking I/O (regular database queries, file reads, calls to libraries that aren't async-aware). FastAPI handles the threading for you.
- **`async def`** — use when your function uses `await` with async libraries (like `httpx.AsyncClient`, `asyncpg`, async SQLAlchemy). Or when your function does no I/O at all (just returns data).

The worst mistake is putting blocking code inside `async def`. FastAPI won't protect you — it trusts that if you said `async def`, you know what you're doing.

**Try it:** Change one of your existing routes from `def` to `async def`. Run the server — it should work exactly the same. That's because your routes don't do any I/O right now, so both `def` and `async def` are fine.

---

### `The Event Loop` — Why Blocking Matters

To understand why blocking inside `async def` is bad, you need a mental model of how async Python works.

Imagine a single waiter in a restaurant. The waiter takes an order from table 1, sends it to the kitchen, and while the kitchen is cooking, goes to table 2 to take their order. The waiter never stands idle — while waiting for one thing, they handle another. That's the event loop.

Now imagine the waiter decides to cook table 1's meal themselves instead of handing it to the kitchen. They're stuck at the stove. Tables 2, 3, and 4 are all waiting, waving for attention, but the waiter can't help them. That's what happens when you put blocking code inside `async def` — the event loop (the waiter) is stuck doing one thing and can't serve anyone else.

With a regular `def`, FastAPI sends the work to the kitchen (thread pool) automatically. The waiter stays free. That's why `def` is the safer default — FastAPI handles the concurrency for you.

```python
# BAD — blocks the event loop, freezes the server
@router.get("/slow")
async def slow_route():
    time.sleep(5)  # blocking! everything stops for 5 seconds
    return {"message": "done"}

# GOOD — FastAPI runs this in a thread, other requests still work
@router.get("/slow")
def slow_route():
    time.sleep(5)  # blocking, but it's in a thread so it's fine
    return {"message": "done"}

# GOOD — non-blocking async sleep
@router.get("/slow")
async def slow_route():
    await asyncio.sleep(5)  # non-blocking, event loop handles other requests
    return {"message": "done"}
```

**Try it:** Create two test routes — one `async def` with `time.sleep(5)` and one `def` with `time.sleep(5)`. Open two browser tabs and hit the `async` version in both at the same time. Notice how the second request waits for the first to finish. Then try the same with the `def` version — both should complete around the same time because they run in separate threads. Delete the test routes when you're done.

---

### `await` — The Keyword That Makes Async Work

`await` is how you tell Python "this operation takes time, go do something else while I wait." You can only use `await` inside an `async def` function, and you can only `await` things that are "awaitable" (async functions, async library calls, etc.).

```python
import httpx

@router.get("/external")
async def get_external_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
    return response.json()
```

When Python hits `await client.get(...)`, it pauses this function and lets the event loop handle other requests. When the HTTP response comes back, the function resumes from where it paused. No threads needed — one event loop handles many concurrent requests efficiently.

Without `await`, the same call would block:

```python
# This would block — httpx.get() is synchronous
response = httpx.get("https://api.example.com/data")
```

The pattern is always the same: use an async library, `await` its calls, and wrap the route in `async def`.

You won't use `await` much yet — your current routes don't make external calls or use async database drivers. But when you get to the database lessons (SQLAlchemy async) and the final project (httpx calls), this is the pattern you'll use.

**Try it:** Install `httpx` with `poetry add httpx`. Create a route that uses `httpx.AsyncClient` to fetch data from `https://httpbin.org/get` (a free test API that returns info about your request). Use `async def` and `await`. Check the response in Swagger.

---

### `BackgroundTasks` — Fire-and-Forget Work

Sometimes you need to do something after sending the response — send an email, write a log, update a cache. The user shouldn't have to wait for these. `BackgroundTasks` lets you schedule work that runs after the response is sent.

```python
from fastapi import BackgroundTasks

def write_log(message: str):
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")

@router.post("/cards")
def create_card(card: Card, background_tasks: BackgroundTasks):
    background_tasks.add_task(write_log, f"Card created: {card.name}")
    return {"message": f"Created card: {card.name}"}
```

The response is returned immediately. `write_log` runs in the background after the response is sent. The client never waits for it.

A few things to note:

- `BackgroundTasks` is injected the same way as `Depends()` — you add it as a parameter and FastAPI provides it automatically. You don't need `Depends()` for this one though, FastAPI recognizes the type.
- `add_task` takes a function and its arguments: `add_task(function, arg1, arg2, ...)`. Don't call the function yourself — pass it without parentheses. The arguments you pass after the function get forwarded to it when it runs. So `add_task(write_log, "Card created: Strike")` is telling FastAPI "later, call `write_log("Card created: Strike")`." This means your background function needs to accept those parameters — if you pass a string to `add_task`, the function needs a `message: str` parameter to receive it.
- The background function can be a regular `def` or an `async def` — FastAPI handles both.

One important limitation: background tasks run in the same process as your server. They're fine for quick, lightweight work — sending a Slack message, writing a log, invalidating a cache. But if the work is heavy (processing images, sending bulk emails, kicking off a data pipeline that takes minutes), `BackgroundTasks` isn't the right tool. For that, you'd use a dedicated task queue like Celery, which runs work in a completely separate worker process so your server isn't affected.

**Try it:** Add a background task to your `create_card` route that prints a message like `"Card created: Strike"` to the terminal after the response is sent. Hit the endpoint in Swagger and check your terminal — you should see the print appear after you get the response.

---

### `When to Use What` — Decision Guide

Here's how to decide what to use for your routes:

**Use `def` when:**
- Your function uses regular (synchronous) libraries — standard SQLAlchemy, file operations, `requests`, `time.sleep()`
- You're not sure — `def` is the safe default. FastAPI handles threading for you.

**Use `async def` when:**
- Your function uses `await` with async libraries — `httpx.AsyncClient`, async SQLAlchemy, `asyncpg`, `aiofiles`
- Your function does no I/O at all — just returns data, does math, etc. (minor performance benefit from avoiding thread pool overhead)

**Use `BackgroundTasks` when:**
- You need to do work after the response is sent — logging, notifications, cache updates
- The work is lightweight — if it takes more than a few seconds, use a proper task queue instead

For this project, most of your routes will stay as `def` until you start using async database drivers or making HTTP calls with httpx. Don't change things to `async def` just because you can — only do it when you have a reason to `await` something.

---

## Your Task

1. Change one of your simple routes (like `get_card`) to `async def` — verify it still works the same
2. Create two test routes to see blocking in action: one `async def` with `time.sleep(3)` and one `def` with `time.sleep(3)`. Test them by hitting each with two requests at the same time and observing the difference. Delete them when done.
3. Install `httpx` and create a route that fetches data from `https://httpbin.org/get` using `httpx.AsyncClient` and `await`
4. Add a `BackgroundTasks` print to your `create_card` route — verify the print appears in the terminal after the response is sent
