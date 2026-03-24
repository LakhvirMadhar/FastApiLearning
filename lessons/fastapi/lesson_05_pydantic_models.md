# Lesson 05: Pydantic Models

## What We're Doing
Learning how to define structured data schemas using Pydantic — so FastAPI can automatically validate, parse, and document the JSON data coming in and going out of your API.

## Why / Context

Up to now, your endpoints have only received data through the URL — path parameters and query parameters. That works fine for simple things like an ID or a filter. But what happens when a client needs to send you a full object? Like creating a new card with a name, energy cost, type, damage, and description — you can't cram all of that into a URL.

That's what **request bodies** are for. The client sends a JSON object in the body of a POST or PUT request, and your API needs to parse it, validate it, and use it. You could do this manually — pull out each field, check the types, handle missing values — but that's tedious and error-prone.

Pydantic solves this. You define a Python class that describes the shape of your data, and FastAPI uses it to automatically validate incoming requests and serialize outgoing responses. If the data doesn't match the schema, the client gets a detailed 422 error. You write the class once, and validation happens everywhere for free.

## Concepts

### `Pydantic BaseModel` — Defining Your Data Shape

A Pydantic model is a Python class that inherits from `BaseModel`. Each attribute you define becomes a field with a type, and Pydantic enforces those types automatically.

```python
from pydantic import BaseModel

class Card(BaseModel):
    name: str
    energy: int
    card_type: str
    damage: int
```

This says: "A Card must have a `name` (string), `energy` (integer), `card_type` (string), and `damage` (integer)." If someone tries to create a Card with `energy: "fast"`, Pydantic rejects it before your code even runs.

This is similar to how type hints on path parameters gave you free validation in Lesson 04 — but now you're validating entire objects instead of single values.

**Try it:** Define a `Card` model in your `main.py`. Think about what fields a Slay the Spire card has — name, energy cost, type (attack/skill/power), damage, maybe a description. Some should be required, some optional with defaults (we'll cover defaults in a bit, so just make everything required for now).

---

### `Using a Model as a Request Body`

To use a Pydantic model as a request body, add it as a function parameter with the model class as the type hint. FastAPI sees that it's a Pydantic model (not a simple type like `str` or `int`) and knows to look for it in the request body, not the URL.

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Card(BaseModel):
    name: str
    energy: int
    card_type: str
    damage: int

@app.post("/cards")
def create_card(card: Card):
    return {"message": f"Created card: {card.name}", "card": card}
```

When a client sends a POST request to `/cards` with this JSON body:

```json
{
    "name": "Strike",
    "energy": 1,
    "card_type": "attack",
    "damage": 6
}
```

FastAPI automatically parses the JSON, validates every field against the `Card` model, and hands your function a `Card` object. You access fields with dot notation — `card.name`, `card.energy`, etc.

Notice the decorator is `@app.post` now, not `@app.get`. POST is for creating new resources — the client is sending data, not just requesting it. This is the first time you're using a method other than GET.

**Try it:** Create a `POST /cards` endpoint that accepts your `Card` model. Test it in Swagger (`/docs`) — you'll see an input field where you can type JSON. Send a valid card and confirm the response.

---

### `Validation in Action`

If the client sends bad data, Pydantic catches it and FastAPI returns a 422 with a detailed error. For example, sending:

```json
{
    "name": "Strike",
    "energy": "fast",
    "card_type": "attack"
}
```

Two problems here: `energy` is `"fast"` instead of an integer, and `damage` is missing entirely. FastAPI returns something like:

```json
{
    "detail": [
        {
            "loc": ["body", "energy"],
            "msg": "Input should be a valid integer",
            "type": "int_parsing"
        },
        {
            "loc": ["body", "damage"],
            "msg": "Field required",
            "type": "missing"
        }
    ]
}
```

Every validation error is listed with its location (`body` → `energy`), a human-readable message, and the error type. The client gets all the errors at once, not one at a time. You didn't write any of this validation logic — Pydantic did it from your class definition.

**Try it:** Send bad data to your POST endpoint — wrong types, missing required fields. Read the 422 error responses and see how Pydantic describes each problem.

---

### `Optional Fields and Defaults`

Not every field needs to be required. You can make fields optional or give them default values, just like function parameters.

```python
from typing import Optional
from pydantic import BaseModel

class Card(BaseModel):
    name: str
    energy: int
    card_type: str
    damage: int = 0
    description: Optional[str] = None
```

- `damage: int = 0` - has a default value. If the client doesn't include it, damage is 0.
- `description: Optional[str] = None` - truly optional. If not provided, it's `None`.
- `name`, `energy`, `card_type` - no defaults, so they're required.

The client can now send:

```json
{
    "name": "Defend",
    "energy": 1,
    "card_type": "skill"
}
```

And it's valid — `damage` defaults to `0` and `description` defaults to `None`.

**Try it:** Update your `Card` model to have some optional fields and some with defaults. Test in Swagger — send a card with only the required fields and confirm the defaults show up in the response.

---

### `Nested Models` — Objects Inside Objects

Pydantic models can contain other Pydantic models. This is how you represent structured, nested data — like a character that has a list of cards.

```python
class Card(BaseModel):
    name: str
    energy: int
    card_type: str

class Character(BaseModel):
    name: str
    health: int
    cards: list[Card]
```

The `cards` field expects a list of `Card` objects. Pydantic validates the outer `Character` *and* every `Card` inside the list. If one card has a bad field, the whole request fails with a 422 pointing to the exact card and field that's wrong.

The JSON for this would look like:

```json
{
    "name": "Ironclad",
    "health": 80,
    "cards": [
        {"name": "Strike", "energy": 1, "card_type": "attack"},
        {"name": "Defend", "energy": 1, "card_type": "skill"}
    ]
}
```

This is the same nested JSON structure from Lesson 02 — but now Pydantic validates it automatically.

**Try it:** Create a `Character` model that contains a list of `Card` objects. Make a `POST /characters` endpoint that accepts it. Send a character with a few cards and see what happens. Then send one with a bad card in the list and check the error.

---

### `Response Models` — Controlling What You Send Back

You can also use Pydantic models to control what your API *returns*. Add a `response_model` parameter to your decorator:

```python
class CardResponse(BaseModel):
    name: str
    card_type: str
    energy: int

@app.post("/cards", response_model=CardResponse)
def create_card(card: Card):
    return card
```

You sent a full card (with name, energy, card_type, damage, description), but the response only comes back with three fields — `name`, `card_type`, and `energy`. That's the `response_model` doing its job.

Think of it like a bouncer at the door. Your function returns the full card object with everything. But `response_model=CardResponse` says "only let these fields through." Everything else gets stripped before it reaches the client.

Why would you want this? Imagine your card has internal fields like a database ID, a creation timestamp, or admin notes. You don't want to expose those to the client. Instead of manually building a filtered dictionary, you just define a `CardResponse` that only includes the public fields, and FastAPI handles the filtering.

The client never sees what was removed — they only get what `CardResponse` allows.

**Try it:** Create a `CardResponse` that has fewer fields than your full `Card` model. Use it as the `response_model` on your POST endpoint and notice how the response gets filtered. Check Swagger — it'll show the response schema too.

---

### `Multiple Models for the Same Data` — A Common Pattern

In real APIs, you often have slightly different shapes for the same resource depending on the operation:

```python
class EnemyCreate(BaseModel):
    """What the client sends when creating an enemy."""
    name: str
    health: int
    damage: int
    act: int

class EnemyResponse(BaseModel):
    """What the server sends back."""
    id: int
    name: str
    health: int
    damage: int
    act: int
```

The client doesn't send an `id` — the server assigns that. But the response includes it. Having separate models for "what comes in" vs "what goes out" keeps things clean and explicit. This is a pattern you'll use constantly once you add a database.

---

## Your Task

Everything above had inline tasks — if you followed those, you've already done most of the work. Here's the full checklist to make sure you've covered everything:

1. Defined a `Card` model with required and optional fields
2. Created a `POST /cards` endpoint that accepts a `Card` body
3. Tested validation with bad data and read the 422 errors
4. Added optional fields and defaults to your model
5. Created a nested `Character` model with a list of `Card` objects and a POST endpoint for it
6. Used a `response_model` to filter what gets sent back

When it's working, show me your code and we'll review it. Next lesson covers response models and status codes in more depth.
