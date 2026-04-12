# Quiz 02 — Answer Key & Feedback

## Overall Notes

You got the **older material (Lessons 1-5) mostly right** because you've been using those concepts every day since you learned them. The **newer material (Lessons 8-11)** is faded because you haven't practiced it again — exactly what spaced repetition is meant to expose. The fix is simple: revisit Lessons 8 and 11 specifically, then move into Lesson 12 where you'll *use* these concepts (database sessions are dependencies, settings carry the DB URL, project structure holds your models).

**Score breakdown (rough):**
- Section 1 (Recall): 4/6 — solid, you remembered the core ideas
- Section 2 (Response models): 3/4
- Section 3 (Errors): 2/4 — needs review
- Section 4 (Project structure): 3/6 — biggest weak area
- Section 5 (DI): 2/5 — needs review
- Section 6 (async): 3/6
- Section 7 (Config): 5/6 — you actually retained this well
- Bonus: 1/3

---

## Section 1: Recall from Quiz 01

**Q1. ✓ Mostly correct.**

Your answer: 422 = wrong field, 4xx = client error, 5xx = server error.

Correct: 400 means the request was malformed in a way the server can't even parse — bad JSON, missing headers, syntactically broken. 422 means the request *was* parsed, but the data inside it failed validation (wrong type, missing required field, value out of range). FastAPI returns 422 specifically for Pydantic validation failures because the request structure was fine — just the contents were wrong.

Memorizing all status codes isn't the goal, but knowing the difference between **400 (broken request)** and **422 (valid request, invalid data)** matters because they tell the client different things to fix.

---

**Q2. ✓ Correct on the function, missing the analogy.**

Your answer: API key for auth. Don't put it in URL params (serpAPI mistake).

The "real-world analogy" is just: a Bearer token is like a wristband at a concert. The bouncer (server) checked your ID at the door (login), gave you a wristband (token), and now you can walk around freely showing the wristband instead of re-proving who you are at every door. "Bearer" literally means "whoever holds this token" — anyone with it gets in, which is why losing it is the same as losing your password.

The serpAPI point you made is correct and is exactly the OWASP example we're saving for Lesson 18.

---

**Q3. ✓ Correct.**

Your answer breaks it down well:
- `app` - the FastAPI instance
- `.get` - method on the app object that registers a GET route
- `@` - decorator syntax (function wrapper)
- `"/"` - the path

One small clarification: when you said "no additional query or path parameters" for `/`, that's not quite right — `/` just means the URL path is the root. You can absolutely add query parameters to a `@app.get("/")` route. The `/` is about the *path* component of the URL, not whether it accepts other parameters.

---

**Q4. ✗ Wrong direction.**

Your answer: something to do with how Python loads functions top-to-bottom.

Correct: route order matters because FastAPI checks routes in the order they're defined and uses the **first match**. If you have:

```python
@app.get("/cards/{card_id}")    # matches /cards/anything
def get_card(card_id: str): ...

@app.get("/cards/featured")     # never reached!
def get_featured(): ...
```

A request to `/cards/featured` will match the first route, with `card_id="featured"`. The "featured" route is unreachable. Fix: put the **specific** routes (`/cards/featured`) **before** the **dynamic** ones (`/cards/{card_id}`).

It's not about Python's import order — it's about route matching order.

---

**Q5. ✓ Correct on the concept, "resource" definition needed.**

Your answer was right about both models. A "resource" in REST API terminology is just **the thing your API exposes** — a card, a user, a comment. Each resource typically has multiple representations:
- `CardCreate` — what the client sends *in* (no `id` because it doesn't exist yet)
- `CardResponse` — what the client gets *out* (includes `id`, hides internal fields like `created_by_user_id`)
- `CardUpdate` — for partial updates, all fields optional

So when I say "the same resource", I mean "the same conceptual thing" (a Card), but with different shapes for different purposes. You had the intuition right; you were just missing the vocabulary.

---

**Q6. ✓ Correct.**

Both errors identified. 422 status code is right.

---

## Section 2: Response Models and Status Codes

**Q7. ✓ Correct.**

You nailed the core difference. To add depth: `response_model` not only filters the output but also generates the OpenAPI schema for the docs and runs Pydantic validation on the response *before* it goes out. The `-> CardResponse` type hint is just documentation for tools — FastAPI doesn't actually use it for filtering. So if you want filtering + validation + docs, use `response_model`. If you just want type-checking your code, the return type hint is fine.

---

**Q8. ✓ Correct.**

Yes, only the 3 declared fields. The other 7 are silently dropped. This is one of the main use cases — you can return a full database object and let `response_model` filter out the fields you don't want exposed (like password hashes).

---

**Q9. ✓ Mostly correct.**

201 is right. To set it:

```python
@router.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(...):
    ...
```

You set it via the `status_code` parameter on the decorator, and yes — using the `status.HTTP_201_CREATED` enum is preferred over hardcoding `201` because it's self-documenting.

---

**Q10. ✓ Correct.**

All three explained correctly. To formalize:
- **200 OK** — successful GET, PUT, or PATCH where you're returning data
- **201 Created** — successful POST that created a new resource
- **204 No Content** — successful operation with nothing to return (most commonly DELETE)

---

## Section 3: Error Handling

**Q11. ✓ Right idea, missing the technical reason.**

Your answer covered the practical reason (consistent shape for the frontend). The technical reason: when you `raise HTTPException`, FastAPI catches it and converts it into a proper HTTP response with the right status code, the right `Content-Type` header, and a JSON body in the standard `{"detail": ...}` format. If you just `return {"error": "..."}`, you're sending a 200 OK with an "error" key, which means **the client thinks the request succeeded**. The client would have to inspect the body to figure out it actually failed — no automatic error handling, no proper status code, no middleware that knows it's an error.

`HTTPException` is a class from `fastapi` (yes, you guessed right). You raise it, FastAPI does the rest.

---

**Q12. ✗ Almost there but you didn't `raise` it.**

The keyword you missed is `raise`. Just creating an `HTTPException()` does nothing — you have to throw it.

```python
from fastapi import HTTPException, status

@app.get("/cards/{card_id}")
def get_card(card_id: int):
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Card not found"
    )
```

The enum name is `HTTP_404_NOT_FOUND`. The pattern is always `HTTP_{code}_{REASON_PHRASE_IN_CAPS}`.

---

**Q13. ✓ Status code correct, mechanism unclear.**

422 is right. What FastAPI does: when a request body comes in, FastAPI runs your Pydantic model's validation. If validation fails, Pydantic raises a `ValidationError`. FastAPI catches that automatically and converts it into a 422 response with detailed error info (which field failed, what was wrong, what was expected). You don't write any code for this — it happens because you used a Pydantic model in your function signature.

---

**Q14. ✗ Hadn't connected this back.**

A custom exception handler lets you catch a *specific* exception type and decide globally how to respond to it. Two main reasons to use one:

1. **Consistent error shape across your API.** If you want all errors to look like `{"code": "CARD_NOT_FOUND", "message": "...", "trace_id": "..."}`, you don't want to write that dict in every route. Write a custom handler once, raise simple exceptions everywhere, and the handler converts them.

2. **Catching exceptions you didn't raise.** If your code raises a `ValueError` from somewhere deep and you don't catch it, FastAPI returns a generic 500. A custom handler for `ValueError` could turn it into a proper 400 with a clean message.

Example:

```python
@app.exception_handler(MyCustomError)
def my_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"code": exc.code, "message": exc.message})
```

---

## Section 4: Project Structure

**Q15. ✓ Correct.**

Right answer. Maintainability + finding stuff fast.

---

**Q16. ✗ Half right.**

You guessed prefixes might stack. They actually do! If you set `prefix="/loot_table"` on `APIRouter()` and then `app.include_router(router, prefix="/cards")`, your routes end up at `/cards/loot_table/...`. Both prefixes get concatenated.

But that's not the **main** difference. The main difference is **where the config lives**:
- `APIRouter(prefix="/cards")` — the router file owns its config. Open `cards.py`, immediately see "this handles `/cards`".
- `app.include_router(prefix="/cards")` — config lives in `main.py`. Centralized, easier to see all prefixes in one place.

Both are valid; pick one and be consistent. Tags work the same way — they don't "nest" in Swagger though, they just show up as a flat list of categories.

---

**Q17. ✗ "Just because" isn't the answer I wanted.**

The reason: FastAPI's `tags` parameter is typed as `list[str | Enum] | None`. The type hint is the contract. A plain string would technically be iterable (Python treats strings as sequences of characters), so passing `tags="Cards"` wouldn't crash — it would silently treat each character as a separate tag, giving you tags `["C", "a", "r", "d", "s"]`. That's why the lesson said "must be a list" — to prevent that silent footgun.

So the deeper answer: it's a list to enforce that you're explicit about wrapping single tags, because the alternative fails silently in a confusing way.

---

**Q18. ✓ Mostly right.**

`__init__.py` marks a folder as a Python package, which makes it importable. Without it, in modern Python you *can* sometimes still import from the folder (called "implicit namespace packages") but it's flaky and depends on tool config. Always include `__init__.py` — it's the safe, standard way.

---

**Q19. ✗ This was actually covered in Lesson 8b — re-read it.**

The reason isn't relative imports. It's about **where you run uvicorn from**. When you run `uvicorn src.main:app` from the project root, Python's "starting point" (`sys.path[0]`) is the project root. So `from src.schemas.cards import Card` works because there's a `src/` folder in the root.

If you ran it from inside `src/` instead, the starting point would be `src/`, and `from src.schemas.cards` would fail because there's no `src/` *inside* `src/`. You'd have to write `from schemas.cards import Card`.

Imports are resolved relative to wherever you ran the command. That's it.

This is worth re-reading Lesson 8b for — it'll matter again in Lesson 12 when you start importing models from `src/models/`.

---

**Q20. ✓ Correct.**

You explained the mechanism perfectly.

---

## Section 5: Dependency Injection

**Q21. ✗ Wrong example, but right intuition about lifecycle.**

The yield example you remembered is for **dependencies with cleanup** (like opening a DB connection, doing work, then closing it). That's a more advanced pattern.

The basic flow for a regular dependency:
1. FastAPI inspects your route function and sees `Depends(some_function)` on a parameter.
2. It looks at `some_function`'s signature to figure out what *it* needs (e.g., `skip` and `limit` from query params).
3. When a request comes in, FastAPI extracts those values from the request, calls `some_function(skip=..., limit=...)`, and injects the **return value** into your route as that parameter.
4. Your route runs with the dependency result already in hand.

You never call the dependency function yourself — FastAPI does it for you and hands you the result.

---

**Q22. ✗ Misread the question.**

The question was asking: when you use `pagination_params` as a dependency, where do `skip` and `limit` get their values from on each incoming request?

Answer: **the URL query string**. Because `pagination_params(skip: int = 0, limit: int = 10)` declares them as plain function parameters with type hints, FastAPI treats them the same way it would if they were in your route function — it pulls them from the query parameters of the request. So a request to `/cards?skip=10&limit=5` would call `pagination_params(skip=10, limit=5)`.

This is the magic: the dependency function "absorbs" what would otherwise be route parameters, so your route signature stays clean.

---

**Q23. ✓ Correct.**

Both points right. To add: parameter-level dependencies pass their return value into the function. Router-level dependencies *run* but their return value is **not** injected. So router-level is for "gatekeeper" stuff like auth checks, where you don't need the return value, you just need the check to pass.

---

**Q24. ✓ Correct guess.**

Yep, a sub-dependency is a dependency that itself has `Depends()` parameters. FastAPI resolves the whole chain.

Use case: authentication. You have:
- `extract_token(request)` — pulls the token out of the `Authorization` header
- `verify_token(token = Depends(extract_token))` — checks the token is valid
- `get_current_user(token_data = Depends(verify_token))` — looks up the user from the verified token

Then your route just does `user = Depends(get_current_user)`. FastAPI runs all three in order and you only see the final result.

---

**Q25. ✓ Correct.**

Both points right. Pydantic models give you `.attribute` access (cleaner than `["key"]`), runtime validation, and auto-completion in your editor.

---

## Section 6: async vs sync

**Q26. ✓ Right idea, fuzzy.**

The cleaner rule: use `async def` only when you're going to `await` something inside it (like an async database call or `httpx.AsyncClient`). If you're not awaiting anything, just use `def` — FastAPI will run it in a thread pool. The reason: putting blocking code inside `async def` freezes the entire server's event loop.

Default to `def`. Switch to `async def` only when you have something to `await`.

---

**Q27. ✓ Right idea, missing the term.**

The term you wanted: **blocks the event loop**. A FastAPI server runs on a single async event loop that handles all requests. If you put `time.sleep(5)` inside an `async def` route, that single event loop is stuck for 5 seconds — meaning **no other request to your entire server can be processed during those 5 seconds**, not even unrelated routes. That's why it's bad: one slow route freezes everything.

The fix is either using `asyncio.sleep(5)` (which yields control back to the loop) or making the route a regular `def` (which FastAPI runs in a thread, not on the loop).

---

**Q28. Missed the question.**

When you write a regular `def` route, FastAPI runs it in a **thread pool**. It assumes a `def` route might do something blocking, so instead of running it on the main event loop (which would freeze the server), it spawns a thread to handle it. Other requests can keep flowing on the main loop while your blocking route does its thing in its thread.

This is why `def` routes are the safe default. You can do blocking I/O (like a regular database call) without worrying about freezing the server, because FastAPI is automatically handling the threading for you.

---

**Q29. ✗ Vague.**

`BackgroundTasks` is for work that should happen **after** the response is sent. The point is the user shouldn't have to wait for it. Examples:
- Send a "thanks for signing up" email after a POST /signup
- Write to a log file after a transaction
- Invalidate a cache after an update
- Trigger a webhook to another service

Without it, the user's request waits for the email to send before getting a response. With it, the response goes out immediately and the email sends in the background.

---

**Q30. ✓ Correct.**

Yep, after the response is sent. That's the whole point.

---

**Q31. ✓ Right intuition, missing the alternative.**

The alternative is a **task queue** like **Celery**, **arq**, or **Dramatiq**. These run a separate worker process (or many workers, possibly on other machines). The web server just adds a job to a queue and moves on; the worker picks it up and processes it.

Why not BackgroundTasks for heavy work? Because BackgroundTasks runs in the same process as your web server. A 10-minute video processing task would tie up resources on your web server for 10 minutes. With Celery, the web server is free immediately and the worker handles the long task elsewhere.

---

## Section 7: Configuration

**Q32. ✓ Both reasons valid.**

Your two reasons (security + the "change once, change everywhere" problem) are exactly right. A third reason worth knowing: different environments need different values (your local DB URL is not the same as production's).

---

**Q33. ✓ Mostly right.**

It looks for `DATABASE_URL` (uppercase, same name). pydantic-settings does case-insensitive matching automatically — your Python attribute is `database_url`, the env var is `DATABASE_URL`. The library handles the case conversion behind the scenes.

---

**Q34. ✓ Correct.**

Yep — Pydantic raises a validation error at startup. The app crashes immediately, which is what you want (fail fast) instead of crashing later with a confusing error.

---

**Q35. ✓ Correct.**

Right. To add: `SecretStr` only hides the value when *displayed* (in logs, repr, str). To get the actual value in your code, you call `.get_secret_value()` on it.

---

**Q36. ✓ Correct, with great practical context.**

Your "30 seconds until the bots find it" point is real — there are bots that scrape new GitHub pushes for AWS keys, Stripe keys, etc. and start using them within minutes. Your point about `.env.example` is right too.

---

**Q37. ✗ Backwards.**

Real environment variables **win over** `.env` entries. The lookup order is:
1. Real environment variable (e.g., set in your shell or by your hosting platform)
2. `.env` file entry
3. The default in the `Settings` class

This is intentional: in production, your hosting platform (Render, Railway, etc.) sets real environment variables, and those should override whatever's in any `.env` file. Local dev uses `.env`, production uses real env vars. Same code, different sources.

---

## Bonus

**B1. Skipped.**

The answer:
```python
@router.get("/blessings")              # list all
@router.get("/blessings/{id}")         # get one
@router.post("/blessings")             # create
@router.put("/blessings/{id}")         # full replace
@router.patch("/blessings/{id}")       # partial update
```

For "just update the description," you use `PATCH` because it's a partial update — the client only sends the field they want to change. With `PUT` they'd have to send the entire blessing object.

---

**B2. ✓ Mostly right but the framing is off.**

The actual issue: `get_current_user` takes `token: str` as a regular parameter. With no other declaration, FastAPI treats it as a **query parameter**. So locally if you happen to be testing without auth, it might work because you're passing `?token=...` as a query string. In production, that won't be how tokens come in — they come in via the `Authorization` header.

The fix: use `Header()` to pull it from headers explicitly, or better, use FastAPI's `OAuth2PasswordBearer` (which you'll see in Lesson 16).

```python
from fastapi import Header

def get_current_user(authorization: str = Header(...)):
    token = authorization.replace("Bearer ", "")
    user = lookup_user(token)
    return user
```

Linters won't catch this — it's a runtime/semantic issue, not a syntax issue.

---

**B3. ✓ Correct.**

Yep. Open Swagger, hit the endpoint, set `?limit=101`, and confirm you get a 400 error with the "Limit cannot exceed 100" message. Easy verification.

---

## What to Revisit

Based on this quiz, here's where to spend time before moving on:

1. **Lesson 8 + 8b** — re-read the imports section. The "where you run uvicorn from determines your import paths" concept didn't stick yet.
2. **Lesson 9** — re-read the basics of how `Depends()` works. You're stuck on the yield pattern, but the simpler "FastAPI calls the function and injects the result" flow needs to click first.
3. **Lesson 10** — re-read the section on what FastAPI does with `def` vs `async def` under the hood. The thread pool vs event loop distinction is the core idea.
4. **Lesson 7** — quick re-read on `raise HTTPException` syntax. You forgot the `raise` keyword.

Everything else you have well enough to keep going. Don't let the gaps stop you — just earmark these for a re-read before Lesson 12 (since database stuff will use sessions-as-dependencies and you'll want DI fresh).
