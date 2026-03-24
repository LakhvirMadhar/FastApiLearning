# Quiz 01 Answers — Lessons 01–05

## Section 1: HTTP Fundamentals (Lessons 01–02)

**Q1.**
POST - create a document at endpoint
PUT - update a document at endpoint
GET - retrieve data from the endpoint
DELETE - delete data at endpoint


**Q2.**
Idk actually. I thought it would be 200. I didn't really memorize the numbers outside of 200, 404, and 422.

**Q3.**
422 - you're entry was wrong
400 - idk what this means actually other than that 4xx series is failure by client

**Q4.**
This is a json object?

**Q5.**
This is for an API token for authentication?

**Q6.**
idk actually. GET request without any parameters vs with?

**Q7.**
Idk, i don't recall covering this


**Q8.**
??? Json is a dictionary with key value pairs?

**Q9.**
{"user": "username", "bookmark": 4, "bookmark":10 }


---

## Section 2: FastAPI Basics (Lesson 03)

**Q10.**
fastapi[standard] and uvicorn.

fastapi for making the actual endpoints + docs. uvicorn for hosting the server.

**Q11.**
it creats a fastAPI object with its methods. app is important cause it's the convention ppl are used to (could call it banana, but app is more appropriate)

**Q12.**
app is the fast api object.
@ is the decorator method for the get method.
get itself, idk what happens under the hood, but it's gets the function that's under it, as @ is a wrapper.
"/" means it's the root repository

So we are going to do whatever the function under @app.get("/") does, which should be the root of the server/API

**Q13.**
--reload just makes sure changes in ur code is reflected in your local server so you don't have to reload the server everytime you type something.
you wouldn't od this in prod, it expects stability

**Q14.**
/docs
i always just click the link uvicron givs and then do /docs.

could also do /redocs

**Q15.**
idk actually? i just thought it sends the dictionary to the client?


---

## Section 3: Path and Query Parameters (Lesson 04)

**Q16.**
You know what idk actually.
path parameter has no placeholder. query parameter does, which allows for retrievinging different info in the same endpoint?

# path
@app.get("/items")

# query
@app.get("/items/{item_id}")


**Q17.**
characters and cards are path
character_name is query
idk how fast api knows actually. Is it because the function has 2 fields that are pre-defined? idk what you call it in python

**Q18.**
422, because they gave a string, not an int.

**Q19.**
It's like python functions. whatever function is declared first is processed by fastAPI. 

**Q20.**
Did you put it as Optional[str] as a parameter in the python function

**Q21.**
Although we did paginationation, honestly, we should revist this later. why? we didn't really use this in a real world scenario.
skip is like you skip the first n amount. limit is how much to return at once.

**Q22.**
path is when there's no customization?
query is when you need to get specific data, like a specific card id?


---

## Section 4: Pydantic Models (Lesson 05)

**Q23.**
a pydantic model is a class for making structured outputs.

**Q24.**
cause in your function, you say the class as what you're expecting.
example

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Card(BaseModel):
    name: str
    energy: int
    description: str

app = FastAPI()

@app.get("/card")
def get_card(card:Card):
    return {"message": card}
```
or was it actually:

```python
from fastapi import FastAPI
from pydantic import BaseModel

class Card(BaseModel):
    name: str
    energy: int
    description: str

class CharacterDeck(BaseModel):
    deck: list(Card)

app = FastAPI()

@app.get("/character/{character_name}")
def get_card(character_name: str, health: int):
    return {
        "name": card,
        "health": int,
        "deck": CharacterDeck.deck
        }
```

**Q25.**
```python
from typing import Optional
from pydantic import BaseModel

class Enemy(BaseModel):
    name: str
    health: int
    attack: int
    act: int
    is_boss: Optional[bool] = False
```

**Q26.**
1. energy is an int, not a string.
2. missing damage parameter


**Q27.**
response_model is a pydantic class that returns only select fields, for reasons like privacy or PII as part of the response the server gives back to the client.

**Q28.**
CardCreate can have all the metadata, including sensitve info.
CardResponse would be a cleaned version without it

**Q29.**
It means it's optional, you don't have to include it in order to call a function. It will be listed on the API, but again, as optional.
I see fastAPI return it as null.

**Q30.**
You get a 422 error because its can't be processed properly.

A nested pydantic model let's you do more typing beyond just primitive types.

Example:

```python
from pydantic import BaseModel

class CardType(BaseModel):
    ATTACK = 'attack'
    SKILL = 'skill'
    POWER = 'power'
    CURSE  = 'curse'
    STATUS = 'status'

class Card(BaseModel):
    name: str
    attack: int
    description: str
    card_type: CardType

class Deck(BaseModel):
    deck = list(Card)

```

---

## Bonus

**B1.**

**B2.**

**B3.**
