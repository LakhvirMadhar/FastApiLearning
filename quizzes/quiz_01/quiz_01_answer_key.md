# Quiz 01 Answer Key — Lessons 01–05

## Section 1: HTTP Fundamentals (Lessons 01–02)

**Q1.** What are the four main HTTP methods and what does each one do?

- **GET** - retrieve/read data from the server. No body sent.
- **POST** - create a new resource. Body contains the new data.
- **PUT** - update/replace an existing resource. Body contains the updated data.
- **DELETE** - remove a resource. Usually no body sent.

The pattern: GET and DELETE point at things ("give me that" / "remove that"). POST and PUT send data ("here's something new" / "here's an update").

---

**Q2.** A client sends a POST request to create a new user, and it succeeds. What status code should the server return — and why not just 200?

**201 Created.** 200 just means "it worked." 201 is more specific — it means "it worked *and* a new resource was created." The distinction tells the client exactly what happened. When you're creating something (POST), 201 is the correct success code because it communicates that a new thing now exists on the server.

---

**Q3.** What's the difference between a 400 and a 422 status code?

- **400 Bad Request** - the server can't even understand what you sent. The request itself is malformed — like sending broken JSON that can't be parsed, or a completely nonsensical request.
- **422 Unprocessable Entity** - the server understood your request (the JSON is valid), but the data inside doesn't pass validation. Wrong types, missing required fields, etc. This is the one FastAPI returns when Pydantic validation fails.

The difference: 400 = "I can't read this," 422 = "I can read it but the data is wrong."

---

**Q4.** What does the `Content-Type: application/json` header tell the server?

It's a header (not the data itself) that tells the server "the body I'm sending you is in JSON format." Without it, the server wouldn't know how to interpret the raw data in the body. It's just one of the key-value pairs in the headers section alongside `Host`, `Authorization`, etc. In API work it's almost always `application/json`, but other values exist like `text/html` for web pages or `multipart/form-data` for file uploads.

---

**Q5.** What does the `Authorization: Bearer <token>` header do? What's a real-world analogy for it?

It proves who you are to the server. The `Bearer` part is a convention meaning "here's a token." The token is a long string the server gave you when you logged in.

**Analogy:** A wristband at a concert — you show it to prove you're allowed in. You don't re-enter your username and password every time, you just flash the token.

---

**Q6.** When does an HTTP request have a body, and when does it not? Give examples using HTTP methods.

It depends on the HTTP method:
- **POST and PUT have bodies** — you're sending data to the server (creating or updating something). The body contains that data.
- **GET and DELETE usually don't have bodies** — you're just pointing at a resource ("give me this" or "remove this"). The URL itself identifies what you want.

This isn't a hard rule (technically you *can* send a body with GET), but in practice this is how APIs work.

---

**Q7.** What is a REST API? How are endpoints typically organized?

REST (Representational State Transfer) is a style of API design. The core idea: organize your API around **resources** (the "things" your API manages — users, cards, bookmarks) and use HTTP methods the way they were intended.

Each resource gets its own URL path, and the HTTP method says what to do with it:
```
GET    /cards        → list all cards
POST   /cards        → create a card
GET    /cards/5      → get card #5
PUT    /cards/5      → update card #5
DELETE /cards/5      → delete card #5
```

REST isn't a strict rule book — it's conventions that make APIs predictable. When you see a new REST API, you can usually guess the endpoints because they all follow this pattern.

---

**Q8.** Name three differences between JSON and Python syntax.

1. **Booleans:** JSON uses `true`/`false` (lowercase). Python uses `True`/`False` (capitalized).
2. **Null/None:** JSON uses `null`. Python uses `None`.
3. **Keys:** JSON keys must be in double quotes (`"name"`). Python dict keys don't require quotes if they're variables, and can use single quotes.

Other differences: JSON only allows double quotes for strings (not single quotes), and JSON does not allow trailing commas.

---

**Q9.** How would you represent a user who has multiple bookmarks in JSON? Write out the structure.

```json
{
    "username": "alex",
    "bookmarks": [
        {"id": 1, "title": "FastAPI Docs", "url": "https://fastapi.tiangolo.com"},
        {"id": 2, "title": "Python Docs", "url": "https://docs.python.org"}
    ]
}
```

The bookmarks are a **list** (array) of objects nested inside the user object. You can't use duplicate keys in JSON — `"bookmark": 4, "bookmark": 10` would just overwrite the first one. Use an array instead.

---

## Section 2: FastAPI Basics (Lesson 03)

**Q10.** What two packages do you need to run a FastAPI app, and what does each one do?

- **FastAPI** - the framework itself. Handles routing, validation, request/response handling, and auto-generates documentation.
- **Uvicorn** - an ASGI server. FastAPI doesn't know how to listen on a port and handle network connections on its own. Uvicorn is the engine that actually runs your FastAPI app and makes it reachable over HTTP.

You always need both — FastAPI is the framework, Uvicorn is the server.

---

**Q11.** What does `app = FastAPI()` create, and why is the variable name `app` important?

It creates the central FastAPI application object. All your routes, middleware, and configuration attach to this object — it's the heart of your API.

The variable name `app` matters because Uvicorn needs to find it. When you run `uvicorn src.main:app`, the `:app` part tells Uvicorn "look for the variable called `app` in that file." You could name it something else, but `app` is the universal convention across FastAPI projects.

---

**Q12.** In `@app.get("/")`, what is `@app.get` doing? Break down what each part means.

- `app` - your FastAPI object (created with `app = FastAPI()`)
- `.get` - one of the HTTP method functions built into that object (there's also `.post()`, `.put()`, `.delete()`)
- `("/")` - the URL path this route handles (`/` is the root)
- `@` - Python's decorator syntax. It takes the function defined below and registers it with FastAPI, so FastAPI knows "when a GET request hits `/`, call this function"

Without the `@` decorator, your function is just a regular Python function that FastAPI doesn't know about.

---

**Q13.** What does `--reload` do in the Uvicorn command, and when would you NOT use it?

`--reload` makes Uvicorn watch your files and automatically restart the server when you save changes. Without it, you'd have to manually stop and restart the server every time you edit code.

You would NOT use it in production. Production expects stability — you don't want the server restarting while handling real user requests. `--reload` is purely a development convenience.

---

**Q14.** What URL do you visit to see FastAPI's auto-generated interactive docs?

- `http://127.0.0.1:8000/docs` - Swagger UI (interactive, has "Try it out" buttons)
- `http://127.0.0.1:8000/redoc` - ReDoc (alternative layout, same info)

FastAPI generates these automatically from your code. As you add routes, they appear in the docs without any extra work.

---

**Q15.** Your function returns a Python dictionary. What does FastAPI do with it before sending it to the client?

FastAPI **converts the Python dictionary to JSON** (serialization) and sends it back as the response body. It also sets the `Content-Type: application/json` header and a `200 OK` status code automatically.

A Python dict and JSON look similar, but they're not the same thing. Python dicts are in-memory objects. JSON is a text format for transmission. FastAPI handles the conversion so you just write Python and the client receives JSON.

---

## Section 3: Path and Query Parameters (Lesson 04)

**Q16.** What's the difference between a path parameter and a query parameter? Give an example URL for each.

**Path parameter** — a dynamic piece of the URL path itself, inside `{}`. It identifies a specific resource.

```
/characters/ironclad        ← "ironclad" is a path parameter
```

**Query parameter** — a key-value pair after `?` in the URL. It filters or modifies the request.

```
/cards?skip=0&limit=10      ← "skip" and "limit" are query parameters
```

Path parameters are part of the URL structure. Query parameters are tacked on after `?` and separated by `&`.

---

**Q17.** In this route, which parameters are path parameters and which are query parameters? How does FastAPI know?

```python
@app.get("/characters/{character_name}/cards")
def get_cards(character_name: str, energy: int = 0, skip: int = 0):
```

- `character_name` — **path parameter** (it appears in the URL as `{character_name}`)
- `energy` — **query parameter** (not in the URL path)
- `skip` — **query parameter** (not in the URL path)

FastAPI decides by checking: is this function parameter name inside `{}` in the path string? If yes → path parameter. If no → query parameter. That's the only rule.

---

**Q18.** What happens if someone hits `/cards/abc` on this endpoint? Why?

FastAPI returns a **422 Unprocessable Entity** error. The route expects `card_id: int`, but `"abc"` can't be converted to an integer. FastAPI uses the type hint to both convert and validate — since the conversion fails, the request is rejected with a detailed error message.

---

**Q19.** Why does route order matter in FastAPI? Give an example of two routes that would conflict if ordered wrong.

FastAPI checks routes top to bottom and uses the first match — just like `if/elif` in Python.

```python
# WRONG order — /cards/random never gets reached
@app.get("/cards/{card_id}")    # FastAPI tries to match "random" as an int
@app.get("/cards/random")       # never reached

# RIGHT order — fixed path first, dynamic path second
@app.get("/cards/random")       # caught first
@app.get("/cards/{card_id}")    # only reached if it's not "random"
```

In the wrong order, FastAPI sees `/cards/random`, matches it against `/cards/{card_id}`, tries to convert `"random"` to an `int`, and returns a 422. Put specific/fixed routes above dynamic ones.

---

**Q20.** What makes a query parameter required vs optional?

Same rule as regular Python functions:

- **Required** — no default value: `skip: int` (client must provide it, or 422)
- **Optional with default** — has a default value: `skip: int = 0` (uses 0 if not provided)
- **Optional with None** — `search: Optional[str] = None` (truly optional, comes back as `None` if not provided)

---

**Q21.** What is pagination and what are the two common styles? Which one uses `skip` and `limit`?

Pagination is how APIs send large datasets in smaller chunks (pages) instead of all at once.

**Two styles:**

- **Offset/limit** — uses `skip` and `limit`. The client says "skip the first 20, give me the next 10." Simple but can get slow with huge datasets because the database still counts through skipped records.
- **Cursor-based** — the API returns a token (cursor) with each response. The client passes it back to get the next page. More efficient for large datasets because the database jumps straight to the right spot.

When building the Gator Days API, you'll consume cursor-based pagination from Reddit and serve offset/limit pagination from your own endpoints.

---

**Q22.** When should you use a path parameter vs a query parameter? What's the quick test to decide?

- **Path parameter** — for identifying a specific resource. `/characters/ironclad` means "the Ironclad character." Without it, the URL doesn't point to anything meaningful.
- **Query parameter** — for filtering, sorting, pagination, search, optional modifiers. `/cards?energy=1` narrows results, but `/cards` on its own still makes sense.

**Quick test:** if removing the parameter makes the URL meaningless, it's a path parameter. If removing it just returns a broader/default result, it's a query parameter.

---

## Section 4: Pydantic Models (Lesson 05)

**Q23.** What is a Pydantic model and what problem does it solve?

A Pydantic model is a Python class that inherits from `BaseModel` and defines the shape of your data — what fields it has, what types they are, which are required, which are optional.

The problem it solves: **automatic validation of incoming data**. Without Pydantic, you'd have to manually check every field in every request — is it the right type? Is it missing? Is it null? Pydantic does all of that from your class definition. If the data doesn't match, the client gets a detailed 422 error listing every problem.

---

**Q24.** How does FastAPI know to look for a Pydantic model in the request body instead of the URL?

FastAPI looks at the **type hint** on your function parameter. If it's a simple type (`str`, `int`, `float`) → path or query parameter. If it's a Pydantic model → request body.

```python
@app.post("/cards")
def create_card(card: Card):  # Card is a BaseModel → FastAPI looks in the request body
```

Also, request bodies go with `@app.post` or `@app.put`, not `@app.get`. GET requests don't have bodies.

---

**Q25.** Write a Pydantic model for a Slay the Spire enemy.

```python
from pydantic import BaseModel

class Enemy(BaseModel):
    name: str
    health: int
    damage: int
    act: int
    is_boss: bool = False
```

All required fields have no default. `is_boss` defaults to `False` so it's optional. Note: `bool = False` is cleaner than `Optional[bool] = False` here, since the value is always `True` or `False`, never `None`.

---

**Q26.** What happens when a client sends this JSON? List all the errors.

Two errors, both caught by Pydantic and returned in a single 422 response:

1. `energy` is `"fast"` (a string) but the model expects `int` → "Input should be a valid integer"
2. `damage` is missing entirely and has no default → "Field required"

The client gets both errors at once, not one at a time. Each error includes its location (`["body", "energy"]`), a message, and an error type.

---

**Q27.** What does `response_model` do on a route decorator? Why would you use it?

`response_model` filters what your API sends back to the client. Even if your function returns a full object with many fields, only the fields defined in the `response_model` class make it into the response. Everything else gets stripped.

Why use it:
- Hide internal fields the client shouldn't see (database IDs, passwords, timestamps)
- Keep responses consistent even if internal data structures change
- Auto-document the response shape in Swagger

---

**Q28.** Why would you have separate `CardCreate` and `CardResponse` models for the same resource?

Because the data shape is different for different operations:

- `CardCreate` — what the client sends when creating a card. No `id` field because it doesn't exist yet — the server/database assigns it.
- `CardResponse` — what the server sends back. Includes `id`, maybe `created_at`, and other server-generated fields.

It's not about hiding sensitive data (though `response_model` can do that too). It's about the fact that "what comes in" and "what goes out" are genuinely different shapes. This pattern shows up constantly once you have a database.

---

**Q29.** What does `Optional[str] = None` mean on a Pydantic field?

It means the field is **truly optional**. The client can omit it entirely, and it will default to `None` (which shows up as `null` in JSON). The `Optional[str]` type hint says "this is either a string or `None`." The `= None` provides the default value.

Compare to `damage: int = 0` — that also has a default, but it's always an integer. `Optional[str] = None` means the value might not exist at all.

---

**Q30.** How do nested Pydantic models work? If a Character has a list of Cards, and one card in the list has bad data, what happens?

Nested models mean a Pydantic model contains another Pydantic model as a field — like `cards: list[Card]` inside a `Character` model.

Pydantic validates the outer model *and* every nested model inside it. If one card in the list has bad data, the entire request fails with a 422 error. The error's `loc` field points to the exact card and field — something like `["body", "cards", 2, "energy"]` meaning "in the body, in the cards list, the third card (index 2), the energy field."
