# Quiz: Lessons 01–05

## Instructions
Answer each question without looking at the lesson docs or your code. Write your answers below each question, then check with me when you're done.

---

## Section 1: HTTP Fundamentals (Lessons 01–02)

**Q1.** What are the four main HTTP methods and what does each one do?

**Q2.** A client sends a POST request to create a new user, and it succeeds. What status code should the server return — and why not just 200?

**Q3.** What's the difference between a 400 and a 422 status code?

**Q4.** What does the `Content-Type: application/json` header tell the server?

**Q5.** What does the `Authorization: Bearer <token>` header do? What's a real-world analogy for it?

**Q6.** When does an HTTP request have a body, and when does it not? Give examples using HTTP methods.

**Q7.** What is a REST API? How are endpoints typically organized?

**Q8.** Name three differences between JSON and Python syntax.

**Q9.** How would you represent a user who has multiple bookmarks in JSON? Write out the structure.

---

## Section 2: FastAPI Basics (Lesson 03)

**Q10.** What two packages do you need to run a FastAPI app, and what does each one do?

**Q11.** What does `app = FastAPI()` create, and why is the variable name `app` important?

**Q12.** In `@app.get("/")`, what is `@app.get` doing? Break down what each part means.

**Q13.** What does `--reload` do in the Uvicorn command, and when would you NOT use it?

**Q14.** What URL do you visit to see FastAPI's auto-generated interactive docs?

**Q15.** Your function returns a Python dictionary. What does FastAPI do with it before sending it to the client?

---

## Section 3: Path and Query Parameters (Lesson 04)

**Q16.** What's the difference between a path parameter and a query parameter? Give an example URL for each.

**Q17.** In this route, which parameters are path parameters and which are query parameters? How does FastAPI know?

```python
@app.get("/characters/{character_name}/cards")
def get_cards(character_name: str, energy: int = 0, skip: int = 0):
```

**Q18.** What happens if someone hits `/cards/abc` on this endpoint? Why?

```python
@app.get("/cards/{card_id}")
def get_card(card_id: int):
    return {"card_id": card_id}
```

**Q19.** Why does route order matter in FastAPI? Give an example of two routes that would conflict if ordered wrong.

**Q20.** What makes a query parameter required vs optional?

**Q21.** What is pagination and what are the two common styles? Which one uses `skip` and `limit`?

**Q22.** When should you use a path parameter vs a query parameter? What's the quick test to decide?

---

## Section 4: Pydantic Models (Lesson 05)

**Q23.** What is a Pydantic model and what problem does it solve?

**Q24.** How does FastAPI know to look for a Pydantic model in the request body instead of the URL?

**Q25.** Write a Pydantic model for a Slay the Spire enemy with: name (required), health (required), damage (required), act (required), is_boss (optional, defaults to False).

**Q26.** What happens when a client sends this JSON to an endpoint expecting the Card model below? List all the errors.

```python
class Card(BaseModel):
    name: str
    energy: int
    card_type: str
    damage: int
```

```json
{
    "name": "Strike",
    "energy": "fast",
    "card_type": "attack"
}
```

**Q27.** What does `response_model` do on a route decorator? Why would you use it?

**Q28.** Why would you have separate `CardCreate` and `CardResponse` models for the same resource?

**Q29.** What does `Optional[str] = None` mean on a Pydantic field?

**Q30.** How do nested Pydantic models work? If a Character has a list of Cards, and one card in the list has bad data, what happens?

---

## Bonus

**B1.** You're designing an API for a library system. Design the REST endpoints (method + path) for: listing all books, getting one book, creating a book, updating a book, and deleting a book.

**B2.** A user hits your API with `/characters/the%20watcher`. What's `%20` and why is it there?

**B3.** What's the difference between `str, Enum` and just `Enum` in Python? Why does FastAPI need the `str` mixin?
