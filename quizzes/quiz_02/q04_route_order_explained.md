# Q4 Deep Dive: Why Route Order Matters in FastAPI

## The Question

> Why does route order matter in FastAPI? Give an example of two routes that would conflict if ordered wrong.

## The Short Answer

FastAPI checks routes in the order you define them and uses the **first one that matches**. If a more general (dynamic) route is registered before a more specific one, the specific one becomes unreachable — the general one always grabs the request first.

## This Is a General Antipattern

This isn't just a FastAPI quirk. It's a well-known antipattern called **unreachable code** or **dead code**, and it shows up in any system that uses "first match wins" logic. Once you recognize it once, you'll see it everywhere.

The exact same trap exists with Python's `try/except` chains. If you catch `Exception` before catching a more specific subtype, the specific one becomes unreachable — every exception inherits from `Exception`, so the broad handler eats them all:

```python
# BROKEN
try:
    do_something()
except Exception as e:        # catches everything, including ValueError
    log("generic error")
except ValueError as e:       # never reached — already caught above
    log("bad value")
```

Fix: specific first, broad last.

```python
# FIXED
try:
    do_something()
except ValueError as e:       # checked first, only catches ValueError
    log("bad value")
except Exception as e:        # catches anything else
    log("generic error")
```

Other common places you'll find the same pattern:

- **Firewall rules** — `allow all` before `deny X` makes the deny rule useless. Same on iptables, AWS security groups, network ACLs.
- **Regex matching pipelines** — broader patterns ordered before specific ones swallow everything.
- **Switch/case statements** in some languages — a fallthrough default before specific cases.
- **URL routing** in Express, Django, Flask, Rails — same problem as FastAPI.
- **Permission systems** — broad role check before specific user override.

The principle is the same in every case: **whenever a system uses "first match wins" logic, specific rules must come before general rules.** Always.

## How Route Matching Actually Works

When a request like `GET /cards/featured` comes in, FastAPI walks through your registered routes one by one in the order they were defined. For each route, it asks: "does this request's method and path match this route's pattern?" The first route that says yes gets the request, and FastAPI stops looking.

That's the key part — **it stops looking on the first match**. There's no concept of "best match" or "most specific match." It's purely the first match wins.

### Where this lives in the source code

If you don't believe me, you can read it yourself. FastAPI's routing actually comes from Starlette (FastAPI is built on top of Starlette and adds Pydantic, dependency injection, OpenAPI, etc.). The relevant file is `starlette/routing.py`, and the matching loop lives inside the `Router.app` method.

Here's a slightly simplified version of the actual code from `starlette/routing.py` (full code is in your venv at `.venv/Lib/site-packages/starlette/routing.py` around line 730):

```python
async def app(self, scope, receive, send):
    ...
    for route in self.routes:
        # Determine if any route matches the incoming scope,
        # and hand over to the matching route if found.
        match, child_scope = route.matches(scope)
        if match == Match.FULL:
            scope.update(child_scope)
            await route.handle(scope, receive, send)
            return
        elif match == Match.PARTIAL and partial is None:
            partial = route
            ...
```

Read that loop carefully. Three things to notice:

1. **`for route in self.routes`** — `self.routes` is a plain Python list. Routes are stored in the order you registered them (`@app.get(...)` and `app.include_router(...)` both append to this list). It's just iteration, no sorting, no priority queue.

2. **`if match == Match.FULL: ... return`** — the moment a route is a full match, it handles the request and the function `return`s. The loop ends. Any routes after the matching one are never even checked.

3. **`Match.PARTIAL`** — there's a partial match concept, but that's only for "the path matches but the method doesn't" scenarios (which is how Starlette generates 405 Method Not Allowed responses). It's not about specificity.

So when the docs say "first match wins," they mean it literally — there's a `for` loop, and a `return` inside an `if`, and that's the entire decision-making process.

### How does the "match" check actually work?

Each route stores a precompiled regex of its path. This happens at startup, in the `compile_path` function (also in `starlette/routing.py`, around line 124). When you write a route like `/cards/{card_id}`, Starlette converts it into a regex like:

```
^/cards/(?P<card_id>[^/]+)$
```

That `(?P<card_id>[^/]+)` is a named capture group that matches one or more characters that aren't a forward slash. In other words, it matches any string between `/cards/` and the end of the path.

When a request comes in, the route's `matches()` method runs that regex against the URL path. If it matches, the captured groups become the path parameter values. For `/cards/featured`, the regex matches and `card_id` gets the value `"featured"`.

A literal route like `/cards/featured` compiles to a regex that has no capture groups:

```
^/cards/featured$
```

That regex only matches one URL: exactly `/cards/featured`. Nothing else.

The thing is, in the broken example, **both** regexes match `/cards/featured`. The dynamic one matches because the regex says "anything after `/cards/`," and the literal one matches because the URL is exactly `/cards/featured`. Whichever route is checked first — by virtue of being first in `self.routes` — wins, and the loop returns before the second one is ever tried.

### Why no "best match" logic?

You might wonder: "Why doesn't Starlette just check all routes, find the most specific one, and pick that?" There are a few reasons:

1. **Performance.** Iterating once and stopping is O(n) on average. Doing best-match logic would mean iterating *all* routes for every request and comparing specificities. For an app with hundreds of routes that's a real cost on every request.

2. **Predictability.** "First match wins" is dead simple to reason about. You read your route file top to bottom and you know exactly what runs. "Best match wins" requires you to have a mental model of which route is "more specific" than another, and that's not always obvious for complex patterns.

3. **Standard practice.** Most web frameworks work this way for the same reasons (Express, Flask, Sinatra). It's the de facto convention for the entire space, so anyone moving between frameworks already understands it.

The downside, of course, is the antipattern this whole document is about. The framework trades a small amount of footgun risk for a lot of speed and clarity.

## The Classic Example

Imagine you want two endpoints under `/cards`:

- `GET /cards/{card_id}` — fetch a card by its ID
- `GET /cards/featured` — fetch the curated list of featured cards

Here's the **broken** version:

```python
@app.get("/cards/{card_id}")
def get_card(card_id: str):
    return {"card_id": card_id}

@app.get("/cards/featured")
def get_featured_cards():
    return {"featured": ["Strike", "Defend"]}
```

What happens when a client hits `GET /cards/featured`?

1. FastAPI checks the first route: `/cards/{card_id}`. The `{card_id}` part is a placeholder that matches **any string**, so `featured` is a valid value for `card_id`.
2. **Match!** FastAPI calls `get_card(card_id="featured")` and returns `{"card_id": "featured"}`.
3. The `get_featured_cards` function is never called. It's effectively dead code.

The user wanted the curated list. They got a useless `{"card_id": "featured"}` payload instead. No error, no warning — just silently wrong behavior. This is the kind of bug that's painful to track down because everything *looks* fine.

### "But aren't these two different endpoints?"

They look like two different endpoints to you, but to FastAPI's URL matcher, `/cards/{card_id}` and `/cards/featured` overlap because `{card_id}` is a wildcard that matches **any string** at that position — including the literal word `"featured"`.

FastAPI doesn't do "smart" matching. It doesn't think "well, `featured` is a literal word in this other route, so I should prefer that." It walks through your routes in order and asks one simple question for each one:

> "Does the incoming URL match this pattern?"

When the URL is `/cards/featured` and the pattern is `/cards/{card_id}`, the answer is **yes**. The pattern says "the path is `/cards/` followed by anything — and that anything becomes the value of `card_id`." The string `"featured"` is a perfectly valid "anything." So `card_id` gets set to `"featured"` and the route handler runs.

### Mental model: think of it as a regex

Think of `{card_id}` as a regex like `/cards/(.+)`. That regex matches:

- `/cards/123` → captures `"123"`
- `/cards/abc` → captures `"abc"`
- `/cards/featured` → captures `"featured"`
- `/cards/literally-anything` → captures `"literally-anything"`

The URL `/cards/featured` matches that pattern because "featured" is just a string and `{card_id}` accepts any string. There's no rule that says "skip this if there's another route with a literal `featured` somewhere else."

So yes — `get_card` and `get_featured_cards` are two different functions, two different endpoints in your code. But from the URL's perspective, they both *could* handle the request `/cards/featured`. FastAPI has to pick one. It picks the first one defined.

### The ELI5 version

Imagine a security guard checking ID at a club. They have a list of rules:

1. "Anyone with an ID can enter the bar area."
2. "VIPs go to the VIP lounge."

A VIP shows up. The guard reads rule 1, sees they have an ID, and sends them to the bar. Rule 2 never gets read because rule 1 already handled the situation. The VIP rule is dead.

To fix it, you reorder the rules:

1. "VIPs go to the VIP lounge."
2. "Anyone else with an ID can enter the bar area."

Now the VIP gets checked first against the VIP rule. Match — they go to the lounge. Regular guests fall through to rule 2.

Same exact problem. Same exact fix. The rules in code work the same as the rules at the club: order matters when you stop checking after the first match.

## The Fixed Version

Put the **specific** route **before** the **dynamic** route:

```python
@app.get("/cards/featured")    # checked first — exact match
def get_featured_cards():
    return {"featured": ["Strike", "Defend"]}

@app.get("/cards/{card_id}")   # checked second — catches anything else
def get_card(card_id: str):
    return {"card_id": card_id}
```

Now when `GET /cards/featured` comes in:

1. FastAPI checks the first route: `/cards/featured`. Exact match? Yes.
2. **Match!** It calls `get_featured_cards` and returns the curated list.

And when `GET /cards/abc123` comes in:

1. FastAPI checks the first route: `/cards/featured`. Match? No (path is `/cards/abc123`, not `/cards/featured`).
2. FastAPI checks the second route: `/cards/{card_id}`. Match? Yes (`card_id="abc123"`).
3. It calls `get_card(card_id="abc123")`.

Both routes work because the specific one is checked first.

## The Mental Rule

When you have routes that share a parent path, follow this order:

1. **Static (literal) paths first** — `/cards/featured`, `/cards/popular`, `/cards/random`
2. **Dynamic (parameterized) paths last** — `/cards/{card_id}`

This way, the static paths get a chance to match before the catch-all dynamic route grabs everything.

## Other Common Variants of the Bug

This issue isn't unique to GET. It happens any time you have a literal path segment that could collide with a dynamic one:

```python
# BROKEN
@app.delete("/users/{user_id}")
def delete_user(user_id: int): ...

@app.delete("/users/me")     # unreachable — /users/me matches the route above
def delete_self(): ...
```

```python
# BROKEN
@app.get("/files/{filename}")
def get_file(filename: str): ...

@app.get("/files/recent")     # unreachable
def get_recent_files(): ...
```

The fix is the same in every case: move the literal route up, the dynamic route down.

## A Subtle Twist: Type Validation Doesn't Save You

You might think: "What if I declare the dynamic param as `int`? Then `/cards/featured` would fail validation and FastAPI would fall through to the next route."

It doesn't. The route still matches first based on the path pattern, then FastAPI tries to validate `featured` as an integer, fails, and returns a **422 Unprocessable Entity** error to the client. It never tries the next route. So even with strict typing, you still get a confusing error instead of the right behavior.

```python
# Still broken!
@app.get("/cards/{card_id}")
def get_card(card_id: int):    # int validation
    return {"card_id": card_id}

@app.get("/cards/featured")
def get_featured(): ...
```

`GET /cards/featured` → 422 error: "card_id should be a valid integer." The featured route is never reached.

## Why This Matters Beyond the Bug

This isn't just a gotcha — it shapes how you organize your route files:

1. **Group related routes together** in the same file (you're already doing this with `routers/cards.py`).
2. **Within each file, order routes from most specific to most general.** Top of the file: literal paths. Bottom of the file: dynamic paths with `{param}`.
3. **When adding a new route, ask: "is there a dynamic route above this that could swallow it?"** If yes, move your new route up.

When you start writing CRUD endpoints in Lesson 13 you'll naturally have routes like `GET /cards`, `GET /cards/{id}`, `POST /cards`, `PATCH /cards/{id}`, `DELETE /cards/{id}`. The order between methods doesn't matter (a `GET` and a `POST` to the same path can never conflict — they're different methods). But within the same method, **literal before dynamic**.

## TL;DR

- FastAPI matches routes in definition order and uses the **first match**.
- A dynamic route like `/cards/{id}` matches **anything** at that position, including literal strings like `featured`.
- If you put the dynamic route first, any specific routes after it become unreachable.
- **Fix:** put specific (literal) routes before dynamic (parameterized) routes.
- Type hints on path parameters won't save you — they cause a 422 instead of falling through.
