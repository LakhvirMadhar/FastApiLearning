# Quiz 02 — Your Answers

## Section 1: Recall from Quiz 01

**Q1.** Idk, uh 422 is wrong entry for the field. 4xx just means you the client made a mistake. I'm not going to memorize all status codes, just that 2xx is some form of OKAY, 4xx is what is said, 5xx is when the server messes up.

**Q2.** This is where you're supposed to pass in your API key. idk what you mean by real world analogy, probably some weird thing you said, that's why you're asking me the analogy part. If you don't do it, you can do OWASP violation, just like serpAPI, which makes you pass it as a parameter & if you get an error message, the API key is in the bloody error messages (idiots).

**Q3.**
- app - FastAPI object
- get() - it's a wrapper on the get method inside the fastAPI object, we know this because of
- @ - decorater method, which means function wrapper.
- "/" - means this is the root (no additional query or path parameters). Of course, if you did what was it, prefix, it would still be root, but in that prefix. Idk wht you call it.

**Q4.** Good question. This was niche, but I do recall facing this issue. It's something to do with how python functions are ordered. If you are trying to do some function but it relies on some other function to exist first, well, python going to load from top to bottom, so you gotta make sure that's not the issue. I don't remember what happens with routes.

**Q5.** I forget the term resource. Please educate me.

`CardResponse` - this is to control the shape of the output of the route (so maybe you don't wanna return certain things)
`CardCreate` - this is the pydantic model that you can pass into a function, that way you have type conformity? that's what i think at least. So like if you want only certain types (such as enum values), you can make it so that only certain stuff is valid.

What that means in terms of resource, idk, i forget what a resource is.

**Q6.** You'll get a 422 error irrc. Problems:
- energy is an int, but user passed a str
- user didn't pass in damage, which was required

---

## Section 2: Response Models and Status Codes

**Q7.** CardResponse is type hinting for mypy/type checking.

The response model will actually make it so your output conforms to the shape you want, allowing you to exlcude fields in the pydantic model.

**Q8.** Only those 3 fields, that's the point, look at answer above

**Q9.** Was it 201? I don't remember how to set codes. It's something in the decorator method where you can set the default code and ensure you are using the enums that come with fastAPI.

**Q10.** Idk, again. Probably should actually take the time to learn each code really.
- 200 - you got stuff back
- 201 - you're post/put request created something
- 204 - You did something, you're not going to expect a response back other than this

---

## Section 3: Error Handling

**Q11.** Good question. Idk. I guess because HTTPException lets you write it to logs properly, it will actually raise a proper error. But what is it actually? is it a method from fastAPI? You can even put the status codes in here for the errors as well.

If you just did "error", well when you go to the frontend, it's gonna have to bloody parse every "error" key and if someone does some other key, welp, app will probably crash. HTTPException gives you an expected, reliable shape to work with.

**Q12.**
```python
from fastAPI import fastAPI, HTTPException, status

app = fastAPI()

@app.get("/")
def my_funct():
    #whaterver
    hmm idk actually how to connect this part
    HTTPException(
        status_code=status.whatveer enum name was 404 is
    )
```

**Q13.** 422. Good question, idk. It type checks the error?

**Q14.** We can do that? i forgot all about it. Idk actually. Guess: you want custom handling for frontend?

---

## Section 4: Project Structure

**Q15.** Clean code and code organization. Last thing you want it to put several thousand of lines in main.py, no one can read it

**Q16.** I didn't know you could do that in APIRouter actually. I'm guessing it changes what the prefix gets added where.

if in app.include_router(prefix="/cards")
but APIRouter(prefix="/loot_table")

it would look like: "/cards/loot_table"?

I guess tags would look nested in the docs too? never had to do that, but that's my guess.

**Q17.** Cause that's what fastAPI expects. idk why, i just follow the rules.

**Q18.** Right, it makes python recognize this is a package for which you can import modules from. Without it, idk you could still import, but then you run into issues of relative imports? Easier to do __init__ instead.

**Q19.** Relative imports, tbh, i don't fully understand this, not really needed for fastAPI itself? This needs to really be it's own lesson plan in a new repo imo.

**Q20.** Let's say you had multiple schemas, like Card, Deck, Map

In your init file, you could import them all in there.

Then when you re-export, you can do

from src.schemas import Card, Deck, Map

---

## Section 5: Dependency Injection

**Q21.** Idk how to explain it in words. I just recall the example being with a db function using yield.

You can call the function to open the db, pauses that function, it goes through whatever you do with the function, then finally closes it.

**Q22.** idk what you mean come's from on each request. Because they have defaults, you don't have to declare it in the function? But you can set them as params I guess?

**Q23.**
- parameter level, only for that function.
- router level, apply to all functions inside the route.

**Q24.** I have no clue. I'm guessing it's a function that depends on another function

**Q25.** For typing reasons that allow for validation that a dictionary object would not easily provide.

And most importanlty, it enforces runtime validation that a type hint doesn't do.

---

## Section 6: async vs sync

**Q26.** Idk actually. I don't remember. When you don't want the thread to wait on just a single function to fully finishing process due to the time it takes for the response to come back due to I/O stuff.

**Q27.** idk the right term, but you now how to wait the full five seconds before the response comes back. Had it been asyncio.time.sleep, whatever that function was, you could make 5 requests and get them all back in about 5 seconds instead of having to wait 25 ish seconds.

**Q28.** ? Not sure what's meant b this

**Q29.** Idk, it's been a while. Just remember something where it was like, hey, send an email after the fact?

**Q30.** After, that's the point.

**Q31.** What to use instead? Not sure. But it's meant for like simple tasks, not something that would take a long time to do.

---

## Section 7: Configuration

**Q32.** You're gonna get hacked. If something changes, you have to change it everywhere.

**Q33.** it's gonna look for database_url in the .env? Idk how it knows, but something to do with the library it imports.

**Q34.** Crash, because no values were set.

**Q35.** Puts passwords as *** to prevent secrets from being leaked

**Q36.** In less than 30 seconds, if your repo is public, attackers will have already gotten it and you're gonna lose money once they start using the key. .env.example is to tell other developers what to put in each field for their local .env field.

**Q37.** The .env key

---

## Bonus

**B1.** dont; wanna

**B2.** In depends, you need to put the value of the parameter. I thought linter would yell at you for this? This probably would have been missed.

**B3.** You put 101 and see if it raises an error.
