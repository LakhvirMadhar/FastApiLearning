# Quiz: Lessons 01–11

## Instructions
Answer each question without looking at the lesson docs or your code. Write your answers below each question, then check with me when you're done. The first section recycles questions from Quiz 01 — you should be able to answer these from memory now that some time has passed. The later sections cover new material from Lessons 06–11.

---

## Section 1: Recall from Quiz 01 (Lessons 01–05)

**Q1.** What's the difference between a 400 and a 422 status code?

**Q2.** What does `Authorization: Bearer <token>` do, and what's a real-world analogy for it?

**Q3.** In `@app.get("/")`, what is `@app.get` doing? Break down what each part means.

**Q4.** Why does route order matter in FastAPI? Give an example of two routes that would conflict if ordered wrong.

**Q5.** Why would you have separate `CardCreate` and `CardResponse` models for the same resource?

**Q6.** A client sends this JSON to a route expecting a `Card(name: str, energy: int, card_type: str, damage: int)`:
```json
{"name": "Strike", "energy": "fast", "card_type": "attack"}
```
What happens? List all the errors.

---

## Section 2: Response Models and Status Codes (Lesson 06)

**Q7.** What's the difference between using `response_model=CardResponse` on the decorator vs just type-hinting the return value as `-> CardResponse`?

**Q8.** Your endpoint returns a Card object that has 10 fields, but your `response_model=CardResponse` only declares 3 of those fields. What does the client receive?

**Q9.** What status code should you return for a successful POST that creates a new resource? How do you set it in FastAPI?

**Q10.** What's the difference between `200 OK`, `201 Created`, and `204 No Content`? When would you use each?

---

## Section 3: Error Handling (Lesson 07)

**Q11.** What's the difference between `raise HTTPException` and just returning a dict with an `"error"` key? Why is `HTTPException` better?

**Q12.** Write the line of code that raises a 404 with the message "Card not found".

**Q13.** What does FastAPI do automatically when a Pydantic validation fails on a request body? What status code does it return?

**Q14.** Why would you write a custom exception handler instead of just raising `HTTPException` everywhere?

---

## Section 4: Project Structure (Lesson 08)

**Q15.** What problem does `APIRouter` solve? Why not just put everything in `main.py`?

**Q16.** What's the difference between setting `prefix` and `tags` on `APIRouter()` vs on `app.include_router()`?

**Q17.** Why does `tags` have to be a list, even when you only have one tag?

**Q18.** What does `__init__.py` do? What happens if you delete it from a folder?

**Q19.** Your `routers/cards.py` has `from src.schemas.cards import Card`. You move the file or change where you run uvicorn from, and the import breaks. Why?

**Q20.** What's a re-export, and when would you use one in `__init__.py`?

---

## Section 5: Dependency Injection (Lesson 09)

**Q21.** What does `Depends()` do? Walk through what FastAPI does when it sees `Depends(some_function)` on a route parameter.

**Q22.** You have a `pagination_params` function that takes `skip: int = 0, limit: int = 10`. When you use it as a dependency, where do `skip` and `limit` come from on each request?

**Q23.** What's the difference between adding a dependency at the parameter level (`Depends()` in the function signature) vs the router level (`APIRouter(dependencies=[...])`)?

**Q24.** What is a sub-dependency, and why is it useful? Give an example use case.

**Q25.** Why would you make your dependency return a Pydantic model instead of a dict?

---

## Section 6: async vs sync (Lesson 10)

**Q26.** What's the rule for when to use `async def` vs `def` for a route function?

**Q27.** What happens if you put `time.sleep(5)` inside an `async def` route? Why is that bad?

**Q28.** What does FastAPI do under the hood when you write a regular `def` route?

**Q29.** What is `BackgroundTasks` for? When would you use it instead of just doing the work inside the route?

**Q30.** When in the request lifecycle does a background task actually run — before the response is sent, or after?

**Q31.** Why is `BackgroundTasks` not a good fit for heavy work like processing a video, and what would you use instead?

---

## Section 7: Configuration (Lesson 11)

**Q32.** Why is hardcoding a database URL in your code a bad idea? List two reasons.

**Q33.** How does pydantic-settings know which environment variable a field maps to? If your field is named `database_url`, what env var does it look for?

**Q34.** What happens at startup if a `Settings` field has no default and the environment variable isn't set?

**Q35.** What does `SecretStr` do, and why use it instead of `str`?

**Q36.** Why should `.env` be in `.gitignore`? What's `.env.example` for?

**Q37.** If you have both an environment variable and a `.env` entry for the same key, which one wins?

---

## Bonus

**B1.** You're designing the routes for a "blessing" feature in your Slay the Spire API. Users can: list all blessings, get one blessing by ID, create a new blessing, update an existing one (full replace), and partially update one (just the description). Write out the five route decorators (method + path) and explain which HTTP method you'd use for the partial update.

**B2.** Imagine you're reviewing a junior dev's PR. They wrote this dependency:

```python
def get_current_user(token: str):
    user = lookup_user(token)
    return user
```

And used it like this:

```python
@router.get("/profile")
def get_profile(user = Depends(get_current_user)):
    return user
```

The route works locally but throws a validation error in production. What's wrong? How would you fix it?

**B3.** You want to test that your `validated_pagination` dependency raises an error when `limit > 100`. Without writing actual test code, describe how you'd test this manually using Swagger.
