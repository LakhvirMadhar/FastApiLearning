# Lesson 13: CRUD Operations

## What We're Doing
Building endpoints that actually create, read, update, and delete data in your Postgres database — replacing the hardcoded dictionaries with real persistence.

## Why / Context

Right now your API is a liar. It has endpoints for creating cards, getting cards, deleting cards — but nothing actually persists. Restart the server and everything is gone. Lesson 12 gave you the database connection and the table. This lesson fills the table with data and reads it back out.

CRUD stands for **Create, Read, Update, Delete** — the four basic operations every API needs. Nearly every route you'll write in any job maps to one of these. Once you know the pattern for one resource (cards), you can repeat it for any resource (characters, users, orders, whatever).

This lesson also introduces the **database session as a dependency** — the `yield` pattern from the Q21 deep dive. Every route that touches the database will use `SessionDep` to get a session. This is where dependency injection stops being abstract and starts being something you use on every route.

## Concepts

### `The Database Session Dependency` — get_db

Every database operation needs a session. You don't want to open and close sessions manually in every route — that's repetitive and error-prone. Instead, you write a dependency that provides a session and cleans it up automatically.

```python
# src/database.py (add this to your existing file)
from typing import Annotated
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SessionDep = Annotated[Session, Depends(get_db)]
```

This is the `yield` dependency pattern from the Q21 deep dive:

1. `db = SessionLocal()` — creates a new database session.
2. `yield db` — pauses the function and hands the session to your route.
3. Your route runs and does its database work.
4. After the route finishes (success or error), `finally: db.close()` runs, closing the session.

`SessionDep` is the `Annotated` alias you'll use in every route. Instead of writing `db: Session = Depends(get_db)` in every single route function, you import `SessionDep` once and use it as a plain type hint. Same pattern as `ValidatedPaginationDep` from Lesson 09 — define once, change in one place if anything ever changes.

```python
from src.database import SessionDep

@router.get("/")
def get_cards(db: SessionDep):
    ...
```

**Try it:** Add `get_db` and `SessionDep` to your `src/database.py` file. You'll use `SessionDep` in every route below.

---

### `Pydantic Schemas vs SQLAlchemy Models` — Two Different Jobs

This is a point of confusion for a lot of people. You now have two things that look similar but serve different purposes:

**SQLAlchemy model** — represents a database table. Lives in `src/models/`. Talks to Postgres.

```python
class Card(Base):
    __tablename__ = "cards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
```

**Pydantic schema** — represents the shape of request/response data. Lives in `src/schemas/`. Talks to clients.

```python
class CardCreate(BaseModel):
    name: str
    cost: int
    description: str | None = None
```

They look similar but they do completely different things. The SQLAlchemy model tells the database what columns exist. The Pydantic schema tells FastAPI what the client should send or receive.

A typical request flow:
1. Client sends JSON → Pydantic schema validates it → you create a SQLAlchemy model instance from it → save to database.
2. Database returns a SQLAlchemy model instance → you return it → FastAPI uses the response Pydantic schema to filter what the client sees.

You'll need these Pydantic schemas for cards:

```python
# src/schemas/cards.py
from pydantic import BaseModel, ConfigDict

class CardCreate(BaseModel):
    """What the client sends to create a card"""
    name: str
    cost: int
    description: str | None = None

class CardResponse(BaseModel):
    """What the API returns"""
    id: int
    name: str
    cost: int
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CardUpdate(BaseModel):
    """What the client sends for a partial update (PATCH)"""
    name: str | None = None
    cost: int | None = None
    description: str | None = None
```

Notice `model_config = ConfigDict(from_attributes=True)` on `CardResponse`. This tells Pydantic: "You can create this model from a SQLAlchemy object by reading its attributes." Without this, Pydantic would expect a dict and fail when you hand it a SQLAlchemy model instance.

Also notice `CardUpdate` — every field is optional. This is for `PATCH` requests where the client only sends the fields they want to change. If they send `{"cost": 3}`, only cost updates. Everything else stays the same.

**Try it:** Update your `src/schemas/cards.py` with `CardCreate`, `CardResponse`, and `CardUpdate`. You already have some schemas there — replace or update them.

---

### `Create` — POST /cards

Creating a record means: take the client's data, make a SQLAlchemy model instance from it, add it to the session, commit, and return the created object.

```python
from fastapi import APIRouter, status
from src.database import SessionDep
from src.models.cards import Card
from src.schemas.cards import CardCreate, CardResponse

@router.post("/", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
def create_card(card: CardCreate, db: SessionDep):
    db_card = Card(
        name=card.name,
        cost=card.cost,
        description=card.description,
    )
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card
```

Step by step:

1. `card: CardCreate` — FastAPI validates the incoming JSON against your Pydantic schema.
2. `db: SessionDep` — FastAPI gives you a database session.
3. `Card(name=card.name, ...)` — create a SQLAlchemy model instance from the validated data.
4. `db.add(db_card)` — tell the session "I want to insert this."
5. `db.commit()` — actually write it to the database.
6. `db.refresh(db_card)` — reload the object from the database so it has the auto-generated `id`.
7. `return db_card` — FastAPI uses `response_model=CardResponse` to serialize it.

The `db.refresh(db_card)` step is easy to forget. After `commit()`, the `id` exists in the database but your Python object doesn't know about it yet. `refresh()` pulls the latest values (including the new `id`) back into the object.

**Try it:** Replace your existing `create_card` route with the database version above. Hit it in Swagger with some test data. Then check pgAdmin — you should see the row in your table.

---

### `Read` — GET /cards and GET /cards/{card_id}

Reading is the simplest operation. Query the database and return the results.

**List all cards (with pagination):**

```python
from src.database import SessionDep
from src.dependencies.pagination import ValidatedPaginationDep

@router.get("/", response_model=list[CardResponse])
def get_cards(pagination: ValidatedPaginationDep, db: SessionDep):
    cards = db.query(Card).offset(pagination.skip).limit(pagination.limit).all()
    return cards
```

`db.query(Card)` starts a query on the cards table. `.offset()` skips rows (for pagination). `.limit()` caps how many rows to return. `.all()` executes the query and returns a list.

Notice how your pagination dependency plugs right in — `skip` and `limit` from the query string flow through the dependency and into the database query. This is where dependencies start paying off.

**Get one card by ID:**

```python
from fastapi import HTTPException

@router.get("/{card_id}", response_model=CardResponse)
def get_card(card_id: int, db: SessionDep):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    return card
```

`.filter(Card.id == card_id)` adds a WHERE clause. `.first()` returns the first match or `None` if nothing matches. If `None`, raise a 404.

**Try it:** Replace your existing `get_cards` and `get_card` routes. Create a few cards via POST first, then test the GET endpoints.

---

### `Update (PUT)` — Full Replacement

`PUT` means "replace the entire resource with what I'm sending." The client sends a complete object, and whatever they send becomes the new state of that resource.

```python
@router.put("/{card_id}", response_model=CardResponse)
def update_card(card_id: int, card: CardCreate, db: SessionDep):
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    db_card.name = card.name
    db_card.cost = card.cost
    db_card.description = card.description
    db.commit()
    db.refresh(db_card)
    return db_card
```

Notice we reuse `CardCreate` as the input schema — the client sends the same shape as when creating. Every field is overwritten. If the client doesn't send `description`, it becomes `None` (the default).

**Try it:** Create a card, then update it with PUT. Check pgAdmin to see the changed values.

---

### `Update (PATCH)` — Partial Update

`PATCH` means "only update the fields I'm sending." This is why `CardUpdate` has all optional fields — the client only includes what they want to change.

```python
@router.patch("/{card_id}", response_model=CardResponse)
def patch_card(card_id: int, card: CardUpdate, db: SessionDep):
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    update_data = card.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_card, field, value)
    db.commit()
    db.refresh(db_card)
    return db_card
```

The key line is `card.model_dump(exclude_unset=True)`. Remember `exclude_unset` from the Pydantic deep dive? It returns only the fields the client actually sent, ignoring fields that were left out. So if the client sends `{"cost": 3}`, `update_data` is `{"cost": 3}` — not `{"name": None, "cost": 3, "description": None}`.

Then `setattr(db_card, field, value)` sets each provided field on the database object. Fields the client didn't send are untouched.

**Why PATCH needs a separate schema:** If you used `CardCreate` for PATCH, `name` and `cost` would be required. The client would have to send everything even if they only want to change the description. `CardUpdate` makes everything optional so the client can send just what changed.

**Try it:** Create a card, then PATCH it with just `{"cost": 5}`. Verify in pgAdmin that only the cost changed and the other fields stayed the same.

---

### `Delete` — DELETE /cards/{card_id}

Delete is straightforward: find the record, remove it, commit.

```python
@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int, db: SessionDep):
    db_card = db.query(Card).filter(Card.id == card_id).first()
    if not db_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Card {card_id} not found",
        )
    db.delete(db_card)
    db.commit()
    return None
```

`db.delete(db_card)` marks it for deletion. `db.commit()` actually removes it. Status 204 means "success, no content to return."

**Try it:** Create a card, delete it, then try to GET it — you should get a 404. Check pgAdmin to confirm it's gone.

---

### `The Pattern` — Every CRUD Route Looks the Same

Look at the routes you just wrote. They all follow the same structure:

1. Get the database session via `SessionDep`.
2. Validate input via Pydantic schema (for POST/PUT/PATCH).
3. Query the database.
4. If the record should exist but doesn't, raise 404.
5. Do the operation (add/update/delete).
6. Commit.
7. Return the result.

Once you've written CRUD for one resource, writing it for another is mostly copy-paste with different model and schema names. This is the bread and butter of backend work — and now you know the pattern.

---

## Your Task

1. Add `get_db` and `SessionDep` to `src/database.py`
2. Update `src/schemas/cards.py` with `CardCreate`, `CardResponse` (with `from_attributes=True`), and `CardUpdate` (all fields optional)
3. Rewrite `src/routers/cards.py` to use real database operations:
   - `POST /` — create a card
   - `GET /` — list all cards with pagination
   - `GET /{card_id}` — get one card by ID
   - `PUT /{card_id}` — full update
   - `PATCH /{card_id}` — partial update
   - `DELETE /{card_id}` — delete a card
4. Remove any hardcoded `cards` dictionary — you don't need it anymore
5. Test every endpoint in Swagger:
   - Create a few cards
   - List them
   - Get one by ID
   - Update one with PUT (send all fields)
   - Update one with PATCH (send only one field, verify others didn't change)
   - Delete one, then try to GET it (should 404)
6. Check pgAdmin after each operation to see the data changing in real time
