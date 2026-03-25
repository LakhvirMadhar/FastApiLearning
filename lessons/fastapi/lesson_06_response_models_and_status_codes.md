# Lesson 06: Response Models and Status Codes

## What We're Doing
Learning how to control exactly what your API sends back — both the shape of the data (response models) and the status code that tells the client what happened.

## Why / Context

In Lesson 05 you got a taste of `response_model` for filtering fields. But there's more to controlling responses than just hiding fields. Right now, every successful response from your API returns `200 OK` — whether you're creating a new card, deleting a character, or just fetching data. That's technically fine, but it's not precise.

A well-designed API uses different status codes to tell the client exactly what happened. `201 Created` after a POST, `204 No Content` after a DELETE, `200 OK` for a GET. These aren't just nice-to-haves — clients and frontend apps often check the status code to decide what to do next. If your API always returns 200, the client has to dig into the response body to figure out what happened.

This lesson is about being intentional with your responses — both the data and the status code.

## Concepts

### `status_code` — Setting the Right Status Code

By default, FastAPI returns `200 OK` for every successful response. You can change this with the `status_code` parameter on your decorator.

FastAPI provides a `status` module with named constants so you don't have to use magic numbers:

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    return {"message": f"Created card: {card.name}", "card": card}
```

Now when a card is created successfully, the client gets `201 Created` instead of `200 OK`. The response body is the same — only the status code changed.

Always use the named constants (like `status.HTTP_201_CREATED`) instead of raw numbers (like `201`). Raw numbers are magic numbers — they require you to remember what `201` means. `status.HTTP_201_CREATED` is immediately readable and self-documenting.

**Try it:** Update your `POST /cards` endpoint to return `201` instead of the default `200`. Check the response in Swagger — you'll see the status code changed.

---

### `Which Status Code When` — A Practical Guide

Here's when to use which status code for your routes:

- `200 OK` - default for GET, PUT. "Here's the data you asked for" or "I updated the thing."
- `201 Created` - for POST. "I created the new thing." Use this whenever your endpoint creates a new resource.
- `204 No Content` - for DELETE (and sometimes PUT). "Done, but I have nothing to send back." The response body is empty.

```python
@app.get("/cards/{card_id}", status_code=status.HTTP_200_OK)
def get_card(card_id: int):
    return {"card_id": card_id, "name": "Strike"}

@app.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    return card

@app.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int):
    # delete logic here
    return None
```

For the DELETE endpoint — notice it returns `None`. With `204 No Content`, there's no response body. The status code alone tells the client "it's done." If you try to return data with a 204, FastAPI will strip it out anyway.

You don't need to memorize every status code. These three cover most of what you'll build. The error codes (400, 404, 422) come up in the next lesson on error handling.

**Try it:** Add a `DELETE /cards/{card_id}` endpoint to your API with a `204` status code. Also add a `PUT /cards/{card_id}` endpoint that accepts a `Card` body and returns `200`. Test both in Swagger.

---

### `Response Model Recap` — Filtering What Goes Out

You used `response_model` in Lesson 05 to filter fields. Here's a quick recap of why it matters, plus a new pattern.

Without `response_model`, your endpoint returns whatever your function returns — every field, no filtering:

```python
@app.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    return card  # returns ALL fields
```

With `response_model`, you define exactly what the client sees:

```python
@app.post("/cards", status_code=status.HTTP_201_CREATED, response_model=CardResponse)
def create_card(card: Card):
    return card  # still returns the full card internally, but CardResponse filters it
```

You can combine `status_code` and `response_model` on the same decorator. They work independently — `status_code` sets the HTTP status, `response_model` filters the body.

**Try it:** Combine `status_code=status.HTTP_201_CREATED` and `response_model=CardResponse` on your POST endpoint. Verify in Swagger that you get a `201` status code AND the filtered response.

---

### `response_model` with Lists — Returning Multiple Items

When your endpoint returns a list of items, you can use `response_model` with a `list[]` type:

```python
@app.get("/cards", response_model=list[CardResponse])
def get_cards():
    cards = [
        {"name": "Strike", "energy": 1, "card_type": "attack", "damage": 6},
        {"name": "Defend", "energy": 1, "card_type": "skill", "damage": 0},
    ]
    return cards
```

Each item in the list gets filtered through `CardResponse`. So even though the dictionaries have `damage` in them, if `CardResponse` doesn't include `damage`, the client won't see it.

This is useful for list endpoints where you want a lighter response — maybe you don't need every field when browsing a list, only when looking at a single item.

**Try it:** Update your `GET /cards` endpoint to return a hardcoded list of card dictionaries with a `response_model=list[CardResponse]`. Check what Swagger shows for the response schema.

---

### `PUT` vs `POST` — Update vs Create

You've been using `POST` to create things. `PUT` is for updating existing things. The mechanics are almost identical in FastAPI — the difference is the intent.

```python
@app.post("/cards", status_code=status.HTTP_201_CREATED)
def create_card(card: Card):
    # create a new card
    return card

@app.put("/cards/{card_id}", status_code=status.HTTP_200_OK)
def update_card(card_id: int, card: Card):
    # update an existing card
    return card
```

The PUT endpoint takes both a **path parameter** (`card_id` — which card to update) and a **request body** (`card` — the new data). Why both? DELETE just needs to know **which** card to remove — `card_id` is enough. But PUT needs to know **which** card AND **what to change**. If you say "update card 5" — update it to *what*? You need to send the new values. That's why PUT takes a path parameter (which card) and a request body (the new data).

FastAPI handles both just like you learned in Lessons 04 and 05 — path parameters from the URL, Pydantic models from the body.

Right now without a database, you can't actually store or update anything. But the endpoint structure is what matters — you're learning the pattern. When you add a database later, the route stays the same and you just add the database logic inside.

**Try it:** Create a `PUT /cards/{card_id}` endpoint that accepts a path parameter and a Card body. Return the card with the `card_id` included in the response. Test it in Swagger.

---

### `DELETE` — Removing Resources

DELETE endpoints are the simplest — they usually just take an ID and return nothing.

```python
@app.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card(card_id: int):
    # delete logic would go here
    return None
```

A few things to notice:

The function returns `None` because `204 No Content` means the response body is empty. The card is gone, there's nothing to send back. The status code alone confirms success.

You don't need a Pydantic model for the request body — you're just pointing at a resource by its ID and saying "remove it." Same as how GET doesn't need a body.

When you have a database, this is where you'd actually delete the record. For now, it's just the route structure.

**Try it:** Create a `DELETE /cards/{card_id}` endpoint with a `204` status code. Test it in Swagger — notice the response has no body.

---

## Your Task

Here's the full checklist of what you should have after this lesson:

1. `POST /cards` with `status_code=status.HTTP_201_CREATED` and `response_model=CardResponse`
2. `GET /cards` returning a hardcoded list with `response_model=list[CardResponse]`
3. `PUT /cards/{card_id}` accepting a path parameter + Card body, returning `200`
4. `DELETE /cards/{card_id}` returning `204` with no body
5. Tested all endpoints in Swagger and verified the status codes are correct

When it's working, show me your code. Next lesson covers error handling — what happens when things go wrong.
