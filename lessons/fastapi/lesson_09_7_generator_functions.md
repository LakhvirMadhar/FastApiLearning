# Lesson 09.7: Generator Functions and `yield`

## What We're Doing
Understanding what generator functions are, how `yield` works, and why `get_db` uses it — so the database session dependency makes sense rather than being magic.

## Why / Context

`get_db` uses `yield` and that makes it a generator function. If you don't know what that means, `get_db` looks like broken code — it seems to return in the middle of the function and then somehow keeps running after. That's not how normal functions work, and it shouldn't be, because generator functions are a different thing entirely.

This lesson explains what they are from the ground up.

## Concepts

### `Normal Functions` — They Run to Completion

A normal function runs from top to bottom, returns once, and is done. The moment it hits `return`, it's finished. Calling it again starts it from scratch:

```python
def make_greeting(name: str) -> str:
    greeting = f"Hello {name}"
    return greeting
    # function is done, everything is gone
```

Every call to `make_greeting` is a fresh start. There's no memory between calls.

---

### `yield` — Pause and Resume

`yield` is like `return`, but instead of ending the function, it pauses it. The function hands a value out, freezes in place, and waits. The next time something asks for a value, it resumes from exactly where it paused.

```python
def count_up():
    yield 1
    yield 2
    yield 3
```

Calling `count_up()` doesn't run any of that code. It returns a **generator object** — a paused function waiting to be driven:

```python
gen = count_up()
print(next(gen))  # 1 — runs up to first yield, pauses
print(next(gen))  # 2 — resumes, runs up to second yield, pauses
print(next(gen))  # 3 — resumes, runs up to third yield, pauses
print(next(gen))  # StopIteration — no more yields, function is done
```

`next()` is what drives the generator forward. Each call resumes from the last pause point and runs until the next `yield`. When there are no more `yield` statements, it raises `StopIteration`.

This is why calling a generator function with `()` doesn't give you the value — it gives you the generator object. The value only comes out when something calls `next()` on it.

---

### `Why This Exists` — Lazy Evaluation

The most common reason to use generators is to produce values one at a time instead of all at once. If you have a million records to process, you don't want to load all million into memory before you start. A generator produces one, you use it, it produces the next:

```python
def read_large_file(filepath):
    with open(filepath) as f:
        for line in f:
            yield line  # one line at a time, not all at once
```

Python's built-in `range()` works this way. `range(1_000_000)` doesn't create a list of a million numbers — it's a generator that produces the next number when asked.

---

### `try/finally with yield` — The Lifecycle Pattern

Here's where it gets relevant to FastAPI. You can put `yield` inside a `try/finally` block:

```python
def managed_resource():
    resource = acquire_something()
    try:
        yield resource        # pause here, hand resource to caller
    finally:
        release_something()   # runs when the generator is closed
```

What happens:
1. `acquire_something()` runs
2. `yield resource` pauses the function and hands `resource` out
3. The caller uses `resource` for as long as it needs
4. When the caller is done (or if an exception occurs), the generator is closed
5. The `finally` block runs — guaranteed, whether the caller succeeded or crashed

This is exactly `get_db`:

```python
def get_db():
    db = SessionLocal()   # open a session
    try:
        yield db          # hand it to the route, pause here
    finally:
        db.close()        # route is done — close the session
```

The session is open for exactly as long as the route needs it. When the route finishes — successfully or with an error — `db.close()` is guaranteed to run. You don't have to remember to close it. You can't forget to close it. The generator handles it.

This is why `get_db` uses `yield` instead of `return`. With `return db`, the function ends and you have no way to run cleanup code after the route finishes. `yield` keeps the function alive in a paused state so the `finally` block can run later.

---

### `for` Loops and Generators

You can also iterate over a generator with a `for` loop — Python calls `next()` for you automatically until `StopIteration`:

```python
def count_up():
    yield 1
    yield 2
    yield 3

for number in count_up():
    print(number)
# 1
# 2
# 3
```

This is how most generators are used in practice — you rarely call `next()` manually. But FastAPI does call it manually for dependencies, because it needs precise control over when the generator pauses and when it resumes.

---

### `Generator Functions vs Regular Functions` — The Summary

| | Regular function | Generator function |
|---|---|---|
| Contains | `return` | `yield` |
| Calling it | Runs the code, returns a value | Returns a generator object, runs nothing yet |
| Getting values | From the return value | By calling `next()` or iterating |
| Can pause | No | Yes — at every `yield` |
| Cleanup after caller | Not possible | Yes — via `try/finally` around `yield` |

---

## How FastAPI Uses This

FastAPI detects that `get_db` is a generator function (it checks using `inspect.isgeneratorfunction`). When it sees a `yield` dependency, it:

1. Calls `next(gen)` to run up to the `yield` and get the value
2. Injects that value into your route
3. Waits for the route to finish
4. Closes the generator, which triggers the `finally` block

This is the mechanism behind `SessionDep`. The session exists for exactly one request — opened before your route runs, closed after it finishes, with cleanup guaranteed even if your route throws an exception.
