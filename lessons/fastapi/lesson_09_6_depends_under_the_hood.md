# Lesson 09.6: `Depends` Under the Hood

## What We're Doing
Understanding what `Depends` actually does, why you can't just call the function yourself, and what dependency injection really means — so you can explain it confidently to someone else.

## Why / Context

The question that prompted this lesson: if you already have a function, why not just call it directly inside your route instead of wrapping it in `Depends`?

```python
def get_cards():
    pagination = pagination_params()  # just call it directly
    ...
```

If this worked, `Depends` would be pointless. The fact that `Depends` exists and everyone uses it means calling the function yourself doesn't work — or at least doesn't work *well*. Understanding why is the whole lesson.

## What Dependency Injection Actually Is

Dependency injection is a pattern, not a FastAPI thing. The concept predates Python entirely.

The idea: a function should not be responsible for creating the things it needs. Instead, something external creates those things and *injects* them in. The function just declares "I need a thing of this type" and trusts that it'll be provided.

The opposite of dependency injection is **tight coupling** — the function creates its own dependencies, so it's stuck to them. It knows exactly what they are, how to build them, and how to tear them down. Change one thing and you're touching the function too.

```python
def get_cards():
    db = SessionLocal()   # creating its own dependency
    pagination = PaginationParams(skip=0, limit=10)  # creating its own dependency
    ...
    db.close()
```

The function is doing too much — it's both creating its dependencies and using them. If `SessionLocal` changes, you update this function. If 50 routes do this, you update 50 functions.

The goal of dependency injection is **loose coupling** — the function doesn't know or care where its dependencies come from, just that they arrive ready to use. You'll also hear this called **inversion of control (IoC)**: instead of the function controlling the creation of what it needs, that control is inverted and handed to something external. FastAPI's `Depends` system is that external thing.

With dependency injection:

```python
def get_cards(db: SessionDep, pagination: ValidatedPaginationDep):
    # db and pagination were created externally and handed in
    # this function only has to worry about using them
    ...
```

The function declares what it needs. Something external handles creation, lifecycle, and cleanup. That "something external" is FastAPI's dependency injection system — and `Depends` is how you talk to it.

A dependency, then, is anything your function needs from the outside world but doesn't create itself. A database session is a dependency — your route needs it to query data but didn't create the database. An authenticated user is a dependency — your route needs to know who's making the request but didn't verify the token. Pagination parameters are a dependency — your route needs `skip` and `limit` but parsing them from the query string is someone else's job. If your function needs something from the outside world to work, that thing is a dependency.

---

## Why You Can't Just Call the Function Yourself

Here are the three concrete reasons calling `func()` yourself breaks down.

### 1. FastAPI can't see the parameters

FastAPI builds your API's behaviour — including Swagger docs, query parameter parsing, and validation — by inspecting your route function's signature at startup. It reads the parameter names, types, and defaults, and uses that to know what to extract from incoming requests.

If you call `pagination_params()` yourself inside the route:

```python
@router.get("/cards")
def get_cards():
    pagination = pagination_params()  # FastAPI has no idea this needs skip and limit
    ...
```

FastAPI sees a route with zero parameters. It doesn't know `skip` and `limit` exist. They won't appear in Swagger. They won't be extracted from the query string. Your function will always get the defaults.

When you use `Depends`:

```python
@router.get("/cards")
def get_cards(pagination: ValidatedPaginationDep):
```

FastAPI inspects `pagination_params` (via the `Depends` chain) at startup, finds `skip: int = 0` and `limit: int = 10`, and knows to extract those from the query string on every request. Swagger shows them automatically.

**`Depends` exposes the dependency's parameters to FastAPI's request parsing system. Calling the function yourself hides them.**

---

### 2. You can't call a generator function with `()`

`get_db` uses `yield`:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

This makes `get_db` a *generator function*. Calling `get_db()` doesn't return a session — it returns a generator object:

```python
result = get_db()
print(result)  # <generator object get_db at 0x...>
```

To actually get the session out, you'd have to drive the generator yourself:

```python
gen = get_db()
db = next(gen)        # runs up to yield, gives you the session
# ... do your work ...
next(gen)             # runs finally block, closes session — but this raises StopIteration
```

Nobody wants to write that in every route. `Depends` handles the entire generator protocol for you — it calls `next()` to get the value, passes it to your route, waits for the route to finish, then drives the generator to completion so the `finally` block runs. It also handles exceptions properly, ensuring cleanup happens even if your route crashes.

**`Depends` is the only practical way to use `yield` dependencies. You can't replicate it with a plain function call.**

---

### 3. Caching within a request

FastAPI caches dependency results within a single request. If two things in the same request both depend on `get_db`, FastAPI calls `get_db` once and reuses the same session for both. You get one session per request, not two.

If you called `get_db()` manually in multiple places, you'd get multiple sessions, multiple transactions, and potentially inconsistent data within a single request.

```python
# With Depends — one session per request, shared
def get_cards(db: SessionDep, user: UserDep):
    # if UserDep also uses get_db internally,
    # FastAPI reuses the same db session for both

# If you called manually — two separate sessions
def get_cards():
    db1 = next(get_db())  # session 1
    db2 = next(get_db())  # session 2 — different transaction
```

---

## What `Depends` Actually Does — The Internals

When FastAPI starts up and registers your routes, it doesn't just store the route function. For every route, it builds a **dependency graph** — a tree of everything the route depends on, and everything those dependencies depend on.

It does this using Python's built-in `inspect` module:

```python
import inspect
sig = inspect.signature(get_cards)
# sig.parameters gives FastAPI every parameter name, type hint, and default value
```

For each parameter, FastAPI checks:
- Is the default value a `Depends` object? → it's a dependency
- Is the type hint `Annotated` with a `Depends` in the metadata? → also a dependency
- Otherwise → it's a query param, path param, or request body

Then it recurses. If `validated_pagination` depends on `PaginationDep`, FastAPI follows that chain too. It maps the entire tree before the server starts taking requests.

At request time, FastAPI walks the graph bottom-up:
1. Calls `pagination_params` first (no dependencies of its own)
2. Passes the result into `validated_pagination`
3. Passes that result into your route

For generator dependencies (`yield`), FastAPI wraps them in a context manager so cleanup is guaranteed. For regular dependencies, it just calls them and uses the return value. For cached dependencies, it calls them once and reuses the result.

None of this is possible if you call the function yourself — FastAPI only controls what happens through `Depends`.

---

## The Full Mental Model

Dependency injection in FastAPI is:

1. **You declare what your route needs** — via type hints and `Depends`
2. **FastAPI builds a dependency graph** — at startup, using `inspect`
3. **On each request, FastAPI resolves the graph** — calling dependencies in the right order, bottom-up
4. **FastAPI injects the results** — into your route function as arguments
5. **After the route finishes, FastAPI runs cleanup** — `finally` blocks in `yield` dependencies

Your route function is never responsible for creating, managing, or cleaning up its dependencies. It just receives them ready to use. That's dependency injection.

The reason you want this:
- Routes stay simple — they only do what they're supposed to do
- Dependencies are reusable — write `get_db` once, use it in 50 routes
- Lifecycles are managed correctly — sessions open and close at the right time, every time
- Testing is easier — you can swap out dependencies with fakes without touching route code
