# Q5 Deep Dive: What Is a Resource?

## The Question

> Why would you have separate `CardCreate` and `CardResponse` models for the same **resource**?

You answered the "why" correctly but got tripped up on the word "resource."

## A Resource Is Just "The Thing"

In REST API terminology, a **resource** is the thing your API lets clients interact with. That's it. A Card is a resource. A Character is a resource. A Blessing is a resource. A User, a Comment, a File, an Order — all resources.

A resource is a concept, not a specific piece of code. There's no `Resource` class you import. It's just the word API developers use to describe what their endpoints manage.

When someone says "the Card resource," they mean: the collection of endpoints, models, database tables, and business logic that deal with cards. Your API has three resources right now:

- **Card** — `GET /cards`, `POST /cards`, `GET /cards/{id}`, `PUT /cards/{id}`, `DELETE /cards/{id}`
- **Character** — `GET /characters/{name}`, `GET /characters/{name}/cards`, `POST /characters`
- **Blessing** — `GET /neow/blessings`

Each resource typically maps to:
- A **database table** (you'll create these in Lesson 12)
- One or more **Pydantic schemas** (you already have these — `Card`, `CardResponse`, etc.)
- A set of **routes** (your router files)
- A **router file** (`routers/cards.py`, `routers/characters.py`, etc.)

## Why Multiple Models for One Resource?

A single resource often has different shapes depending on the context. A Card looks different when you're creating it vs when you're reading it vs when you're updating it.

### Creating a card (what the client sends in):

```python
class CardCreate(BaseModel):
    name: str
    energy: int
    card_type: CardType
    damage: int
    description: str | None = None
```

No `id` field — the database generates the ID. The client doesn't get to pick it.

### Reading a card (what the API sends back):

```python
class CardResponse(BaseModel):
    id: int
    name: str
    card_type: CardType
    energy: int
```

Now there's an `id` (the database assigned one). But `damage` and `description` might be hidden — maybe they're internal fields, or maybe the list view is intentionally slim for performance.

### Updating a card (what the client sends for a PATCH):

```python
class CardUpdate(BaseModel):
    name: str | None = None
    energy: int | None = None
    card_type: CardType | None = None
    damage: int | None = None
    description: str | None = None
```

Everything is optional — the client only sends the fields they want to change.

### All three are the same resource

`CardCreate`, `CardResponse`, and `CardUpdate` are all about *Cards*. They're different views of the same resource, shaped for different operations. The resource is the abstract concept ("a card in our system"). The models are the concrete shapes it takes in different parts of the request/response cycle.

## Analogy

Think of a person filling out forms at a hospital:

- **Admission form** (like `CardCreate`) — name, date of birth, insurance info. You provide the details, the hospital assigns you a patient ID.
- **Patient wristband** (like `CardResponse`) — patient ID, name, allergies. A simplified view with the key info. Doesn't include your full insurance details.
- **Update form** (like `CardUpdate`) — only fill in what changed. New address? Fill in the address field. Everything else stays the same.

The resource is "the patient." The forms are different shapes of the same resource for different purposes.

## TL;DR

- A **resource** is the conceptual thing your API manages (Card, Character, User, etc.)
- It's not a code construct — it's vocabulary for describing what your API is about
- One resource often has multiple Pydantic models because the same thing has different shapes for creating, reading, and updating
- When someone says "the Card resource," they mean everything related to cards: the routes, the schemas, the database table, the logic
