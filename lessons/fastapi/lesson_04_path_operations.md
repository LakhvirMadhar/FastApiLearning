# Lesson 04: Path Operations

## What We're Doing
Learning how to make your endpoints dynamic — accepting data through the URL itself using path parameters and query parameters.

## Why / Context

Right now your endpoints are static. `/about` always returns the same thing. But real APIs need to handle things like "get me Ironclad's cards" or "search cards that cost 1 energy." The data for those requests lives right in the URL — either as part of the path (`/characters/ironclad`) or as a query string (`/cards?energy=1`).

FastAPI gives you two ways to pull data out of URLs: **path parameters** and **query parameters**. They serve different purposes, and knowing when to use which is important for designing clean APIs.

## Concepts

### `Path Parameters` — Dynamic Pieces of the URL

When you put `{something}` in your route path, FastAPI treats it as a variable. It extracts that piece of the URL and passes it to your function as an argument.

```python
@app.get("/characters/{character_name}")
def get_character(character_name: str):
    return {"character": character_name}
```

If someone hits `/characters/ironclad`, FastAPI extracts `"ironclad"` from the URL and passes it to `get_character` as `character_name="ironclad"`. The response would be:

```json
{"character": "ironclad"}
```

The type hint `str` isn't just documentation here — it's functional. FastAPI uses it to:
1. **Convert** the value from a string (URLs are always strings) to the type you specified
2. **Validate** that the value actually matches that type

If you used `int` instead — say for a card ID like `/cards/{card_id}` — and someone hits `/cards/abc`, they'd get a `422 Unprocessable Entity` error because `"abc"` can't be converted to an `int`. You didn't write any validation code — the type hint did it for you. This is a running theme in FastAPI: type hints are the API contract.

The name inside the curly braces (`{character_name}`) must match the function parameter name (`character_name`). That's how FastAPI knows which URL segment maps to which argument.

---

### `Multiple Path Parameters` — More Than One Variable

You can have multiple path parameters in a single route. Each one becomes its own function argument.

```python
@app.get("/characters/{character_name}/cards/{card_id}")
def get_character_card(character_name: str, card_id: int):
    return {"character": character_name, "card_id": card_id}
```

Hitting `/characters/ironclad/cards/7` would give you:

```json
{"character": "ironclad", "card_id": 7}
```

This pattern is common for representing relationships — "get card 7 that belongs to Ironclad."

It looks a lot like nested folders, and that's a decent mental model for reading URLs. But there's an important difference: folders are about file location, while URL paths are about **resource relationships**. `/characters/ironclad/cards/7` doesn't mean "card 7 is stored inside Ironclad's folder." It means "card 7 *belongs to* Ironclad." The nesting in the URL is a design choice about how you want to express relationships, not a requirement. For example, these two API designs could return the exact same data:

```
GET /characters/ironclad/cards/7    → "get card 7 that belongs to Ironclad" (nested — relationship is in the URL)
GET /cards/7                        → "get card 7" (flat — the server knows internally that card 7 belongs to Ironclad)
```

In a folder system, a file can only live in one place. In an API, the same resource can be reachable through different paths depending on how you design it.

---

### `Query Parameters` — Filtering and Optional Data

Query parameters are the key-value pairs that come after the `?` in a URL, like `/cards?skip=0&limit=10`. They're used for things that aren't part of the resource identity — filtering, sorting, pagination, search terms.

In FastAPI, any function parameter that isn't in the URL path is automatically treated as a query parameter.

```python
@app.get("/cards")
def get_cards(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}
```

The path is just `/cards` — no curly braces. But the function takes `skip` and `limit` as parameters. Since they're not in the path, FastAPI knows they must come from the query string.

Hitting `/cards?skip=5&limit=20` returns:

```json
{"skip": 5, "limit": 20}
```

Notice the `= 0` and `= 10` — those are **default values**. They make the parameters optional. If someone just hits `/cards` without any query string, `skip` defaults to `0` and `limit` defaults to `10`. If a query parameter has no default value, it becomes **required** — FastAPI will return a 422 error if it's missing.

This is the same rule as regular Python functions. If a parameter has no default value, you must provide it when calling the function. FastAPI just extends that to HTTP: if the query parameter is required in the function signature, it's required in the URL.

```python
# Python: skip is required, limit has a default
def get_cards(skip: int, limit: int = 10):
    ...

# Same logic in FastAPI — skip must be in the query string
@app.get("/cards")
def get_cards(skip: int, limit: int = 10):
    ...
```

`/cards?limit=5` would return a 422 because `skip` is missing. `/cards?skip=0` works because `limit` defaults to 10.

---

### `Path + Query Together` — Combining Both

You can mix path parameters and query parameters in the same route. FastAPI figures out which is which based on whether the parameter name appears in the path.

Say you want to get a character's cards, but optionally filter them:

```python
@app.get("/characters/{character_name}/cards")
def get_character_cards(character_name: str, type: Optional[str] = None, energy: Optional[int] = None):
    return {"character": character_name, "type": type, "energy": energy}
```

- `character_name` is in the path (`{character_name}`), so it's a **path parameter** — it identifies *which* character. Without it, the URL is meaningless.
- `type` and `energy` are not in the path, so they're **query parameters** — they filter the results. Without them, you still get a valid response (all cards), just a broader one.

Hitting `/characters/ironclad/cards?type=attack&energy=1` returns:

```json
{"character": "ironclad", "type": "attack", "energy": 1}
```

"Give me Ironclad's attack cards that cost 1 energy."

Hitting `/characters/ironclad/cards` without any query parameters still works — `type` and `energy` just come back as `null` because they default to `None`.

---

### `Optional Query Parameters` — Using `None` as Default

Sometimes a query parameter should be truly optional — not just "has a default value" but "might not be provided at all." You do this by defaulting to `None`.

```python
@app.get("/cards")
def get_cards(skip: int = 0, limit: int = 10, search: Optional[str] = None):
    if search:
        return {"skip": skip, "limit": limit, "search": search}
    return {"skip": skip, "limit": limit}
```

- `skip` and `limit` have numeric defaults — they're always present
- `search` defaults to `None` — it only shows up if the client provides it

`/cards?search=strike` includes the search term. `/cards` on its own doesn't.

The `Optional[str]` type hint (from `typing import Optional`) tells FastAPI (and anyone reading your code) that this parameter is either a string or `None`. You might also see this written as `str | None` — that's the Python 3.10+ syntax and does the exact same thing, just shorter.

---

### `Path vs Query` — When to Use Which

This is a design decision you'll make for every endpoint. The general rule:

- **Path parameters** - for identifying a specific resource. They're part of the URL structure. `/characters/ironclad` means "the Ironclad character." Without it, the URL doesn't point to anything meaningful.

- **Query parameters** - for everything else — filtering, sorting, pagination, search, optional modifiers. They refine the request but the URL still makes sense without them. `/cards` is valid on its own; `?energy=1` just narrows the results.

A quick test: if removing the parameter makes the URL meaningless, it's a path parameter. If removing it just returns a broader/default result, it's a query parameter.

---

### `Pagination` — Why Skip and Limit Matter in the Real World

The `skip` and `limit` query parameters from earlier aren't just a teaching example — they're how real APIs handle **pagination**. When an API has thousands of records (say 10,000 cards across all characters), it doesn't send them all in one response. That would be slow, wasteful, and might time out. Instead, it sends them in pages, and the client requests one page at a time.

There are two common styles of pagination:

- **Offset/limit** (what you just learned) - the client says "skip the first 20 records and give me the next 10." Simple and easy to implement. Your `/cards?skip=20&limit=10` endpoint is already doing this. The downside is it can get slow with huge datasets because the database still has to count through all the skipped records.

- **Cursor-based** - instead of "skip 20," the API gives you a token (called a cursor) with each response that points to where the next page starts. You pass that token back to get the next page. This is more efficient for large datasets because the database can jump straight to the right spot instead of counting from the beginning.

If you've ever scraped an API and had to "paginate through results," this is what was happening — the API was handing you data one page at a time, and you had to keep asking for the next page until there was nothing left.

When you build your Gator Days comic API, you'll be on both sides of this: consuming paginated data from Reddit (cursor-based) and serving paginated data from your own endpoints (offset/limit).

---

### `Route Order` — Why Declaration Order Matters

**Route order matters.** FastAPI checks routes top to bottom in the order they're declared in your file and uses the first match. It works just like `if/elif` in Python — first match wins, everything below is skipped:

```python
def identify(value):
    if value == "special":
        return "It's the special item"
    elif isinstance(value, int):
        return f"It's item number {value}"
```

If you flip the order:

```python
def identify(value):
    if isinstance(value, int):
        return f"It's item number {value}"
    elif value == "special":
        return "It's the special item"  # never reaches here if value matches above
```

FastAPI routes work the same way:

```python
# This order works — "random" is caught first
@app.get("/cards/random")
def get_random_card():
    return {"card": "random pick"}

@app.get("/cards/{card_id}")
def get_card(card_id: int):
    return {"card_id": card_id}
```

```python
# This order breaks — FastAPI tries to match "random" as an int
@app.get("/cards/{card_id}")
def get_card(card_id: int):
    return {"card_id": card_id}

@app.get("/cards/random")  # never reached for /cards/random
def get_random_card():
    return {"card": "random pick"}
```

In the broken version, FastAPI sees `/cards/random`, matches it against `/cards/{card_id}`, tries to convert `"random"` to an `int`, and returns a 422. Put specific/fixed routes above dynamic ones.

---

## Your Task

Build a fake Slay the Spire card API. You don't need real card data — just return dictionaries with hardcoded or constructed data.

1. **Create a route with a path parameter.** Something like `/characters/{character_name}` that returns info about a character.

2. **Create a route with query parameters.** A list endpoint like `/cards` that accepts `skip` and `limit` with default values.

3. **Combine both.** A route like `/characters/{character_name}/cards` that takes the character as a path parameter and optional query parameters for filtering (card type, energy cost, rarity, whatever makes sense to you).

4. **Test type validation.** If you have a route that expects an `int` (like energy cost as a path parameter), try hitting it with a string and see what FastAPI returns. Check the error response — this is that automatic 422 validation in action.

5. **Check the Swagger docs.** Go to `/docs` and notice how FastAPI documents your parameters — it shows which are required, which are optional, and what types they expect. Try the "Try it out" button.

When it's working, show me your code and we'll review it. Next lesson covers Pydantic models — that's where request and response validation gets serious.
