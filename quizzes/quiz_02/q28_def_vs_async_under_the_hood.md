# Q28 Deep Dive: What FastAPI Does With `def` Under the Hood

## The Question

> What does FastAPI do under the hood when you write a regular `def` route?

## The Short Answer

FastAPI runs `def` routes in a **thread pool**, not on the main event loop. This is why `def` is the safe default — you can do blocking work without freezing the server.

## What's a Thread? What's a Thread Pool?

### Thread

The name "thread" comes from the metaphor of a "thread of execution" — a single line of instructions being followed step by step, like following a thread through a maze. Each thread is one independent path through your code.

To understand threads, you need to know what a **process** is first. A process is a running program. When you start uvicorn, that's a process. It gets its own memory, its own Python interpreter, its own everything. It's heavyweight — creating a new process is expensive.

A **thread** is a lighter-weight thing *inside* a process. Multiple threads share the same memory and the same Python interpreter, but each one follows its own path through the code independently. They're cheaper to create and switch between than processes.

### Thread Pool

A thread pool is a collection of pre-created threads sitting around waiting for work. "Pool" because they sit there like a pool of available workers — grab one when you need it, return it when you're done. Python's standard library has one built in (`concurrent.futures.ThreadPoolExecutor`). When uvicorn starts, it creates a thread pool automatically. You never create or manage it yourself.

When FastAPI needs to run a blocking `def` route, it grabs a thread from the pool, runs your function on it, and when it's done, the thread goes back to the pool for the next job.

Here's what your uvicorn server actually looks like:

```
Process (your uvicorn server)
├── Main thread (runs the event loop)
├── Thread pool
│   ├── Thread 1 (idle, waiting for work)
│   ├── Thread 2 (running a def route)
│   ├── Thread 3 (running another def route)
│   └── Thread 4 (idle, waiting for work)
```

The main thread runs the event loop (handles async stuff). The pool threads handle `def` routes.

Think of it like a restaurant with one manager (the event loop / main thread) and a team of cooks (the thread pool). When an order comes in:

- The manager doesn't cook it themselves — that would stop them from taking new orders.
- The manager hands it to an available cook and immediately goes back to greeting customers.
- When the cook finishes, they hand the plate back to the manager, who delivers it.

The manager (event loop) is never stuck waiting. The cooks (threads) do the slow work.

## The Two Paths: `def` vs `async def`

When FastAPI receives a request and needs to call your route function, it checks: is this function `def` or `async def`?

### Path 1: `def` route

```python
@router.get("/cards/{card_id}")
def get_card(card_id: int):
    card = db.query(Card).get(card_id)  # blocking database call
    return card
```

1. Request arrives on the main event loop.
2. FastAPI sees this is a regular `def` function.
3. FastAPI sends it to the **thread pool**: "Hey, run this function on a separate thread."
4. The event loop is **immediately free** to handle other incoming requests.
5. The thread runs `get_card`, which does a blocking database query. The thread waits, but that's fine — it's just one thread, not the main loop.
6. When the database responds, the thread finishes, and the result comes back to the event loop.
7. The event loop sends the response to the client.

**Key point:** the event loop never blocked. While one thread was waiting on the database, the event loop was handling requests from other clients.

### Path 2: `async def` route

```python
@router.get("/cards/{card_id}")
async def get_card(card_id: int):
    card = db.query(Card).get(card_id)  # blocking database call — BAD!
    return card
```

1. Request arrives on the main event loop.
2. FastAPI sees this is an `async def` function.
3. FastAPI runs it **directly on the event loop**. No thread pool.
4. The function hits `db.query(...)` — a blocking call.
5. The event loop is **stuck waiting** for the database to respond.
6. **Every other request to your entire server is frozen** until the database responds.
7. Database responds, function finishes, event loop resumes.

**Key point:** the event loop blocked. No other request could be processed while the database query ran. One slow query freezes the entire server.

### Path 3: `async def` done right

```python
@router.get("/cards/{card_id}")
async def get_card(card_id: int):
    card = await async_db.query(Card).get(card_id)  # non-blocking!
    return card
```

1. Request arrives on the main event loop.
2. FastAPI runs it directly on the event loop.
3. The function hits `await async_db.query(...)`.
4. The `await` tells the event loop: "I'm waiting on something. Go handle other requests. Come back to me when the database responds."
5. The event loop handles other requests while waiting.
6. Database responds, the event loop resumes this function from where it paused.
7. Function finishes, response is sent.

**Key point:** the event loop never blocked because `await` gave it permission to do other work in the meantime.

## Why This Matters

The distinction explains the golden rule from Lesson 10:

| Situation | Use | Why |
|---|---|---|
| Blocking I/O (regular database, file read, `requests` library) | `def` | FastAPI puts it in a thread, event loop stays free |
| Non-blocking I/O (async database, `httpx.AsyncClient`, `asyncio.sleep`) | `async def` + `await` | Runs on the event loop efficiently, no thread overhead |
| No I/O at all (just returns data, does math) | Either works | `async def` is slightly faster (skips thread pool), but the difference is negligible |
| Blocking I/O inside `async def` | **BUG** | Event loop freezes, entire server stops |

## The Visual

```
Request 1 ──→ Event Loop ──→ Thread Pool ──→ [def route runs, blocks on DB]
                  │                              ↓
Request 2 ──→ Event Loop ──→ Thread Pool ──→ [def route runs, blocks on file]
                  │
Request 3 ──→ Event Loop ──→ [async def route runs, awaits, event loop stays free]
                  │
Request 4 ──→ Event Loop ──→ [async def with blocking code — STUCK, everything waits]
```

Requests 1 and 2 are handled safely because `def` routes go to the thread pool. Request 3 is handled efficiently because `await` releases the event loop. Request 4 is the bug — blocking code on the event loop freezes everything.

## What You Saw in Your Test

When you tested `time.sleep(5)` in both `def` and `async def` routes:

- **`def` with `time.sleep(5)`** — two requests finished in ~5 seconds total. Each ran on its own thread in the pool. Both threads slept independently.
- **`async def` with `time.sleep(5)`** — two requests took ~10 seconds total. The first request froze the event loop for 5 seconds. Only after it finished could the second request even start.

That experiment was the proof. You saw the thread pool working vs the event loop blocking.

## When You'll Use This Knowledge

Right now your routes don't do real I/O, so `def` vs `async def` doesn't matter much. But starting in Lesson 12-13:

- If you use **regular SQLAlchemy** (synchronous), keep your routes as `def`. FastAPI threads them safely.
- If you use **async SQLAlchemy** (`AsyncSession`), use `async def` with `await`. Runs on the event loop efficiently.
- If you call external APIs with **httpx**, use `async def` with `await httpx.AsyncClient`.

Most FastAPI tutorials use regular SQLAlchemy with `def` routes. That's perfectly fine and is what we'll do.

## TL;DR

- `def` routes → FastAPI runs them in a **thread pool**, event loop stays free. Safe for blocking code.
- `async def` routes → FastAPI runs them **on the event loop**. Only safe if you `await` everything. Blocking code here freezes the server.
- The thread pool is why `def` is the safe default. FastAPI handles the threading automatically.
- The event loop is a single-threaded task manager that juggles many async tasks by switching between them at `await` points.
