# Lesson 03: Hello FastAPI

## What We're Doing
Installing FastAPI, creating your first API endpoint, and running a development server.

## Why / Context

You've spent two lessons understanding how HTTP and APIs work conceptually. Now you're going to build one. By the end of this lesson, you'll have a running server on your machine that you can send HTTP requests to and get JSON responses back. Everything from Lessons 01 and 02 is about to become real.

FastAPI needs two things to run: the **FastAPI** framework itself and a **server** to actually serve it. FastAPI is the framework — it handles routing, validation, and all the nice stuff. But it doesn't know how to listen on a port and handle incoming network connections. For that, you need **Uvicorn**, which is an ASGI server (think of it as the engine that actually runs your FastAPI app). You'll always install both together.

## Concepts

### `Virtual Environment` — Isolating Your Project

Before installing anything, you need a virtual environment. If you've done Python work before, you probably know this drill — but here's why it matters.

When you `pip install` something, it goes into your Python installation globally. That's a problem if you have two projects that need different versions of the same library. A virtual environment creates an isolated Python installation just for this project. Anything you install inside it stays inside it.

You're using **Poetry** to manage this project, which handles virtual environments for you. Poetry creates and manages the `.venv` automatically — you don't need to manually create or activate it. Poetry also tracks your dependencies in `pyproject.toml` instead of a `requirements.txt` file, which is cleaner and more modern.

#### Commands:

- `poetry install` — installs all dependencies listed in `pyproject.toml` (and creates the `.venv` if it doesn't exist)
- `poetry add <package>` — adds a new package to the project (installs it and updates `pyproject.toml`)
- `poetry shell` — activates the virtual environment in your terminal (you'll see the environment name in your prompt)
- `poetry run <command>` — runs a single command inside the virtual environment without activating it

---

### `poetry add` — Getting FastAPI and Uvicorn

You need to install two packages:

- **fastapi** — the framework itself
- **uvicorn** — the server that runs it

You can install them both in one command with `poetry add`. Poetry will add them to your `pyproject.toml` and install them into the virtual environment. Anyone who clones your project just runs `poetry install` and they're set — Poetry reads `pyproject.toml` and `poetry.lock` to recreate the exact same environment.

---

### `FastAPI()` — Creating the App

Everything in FastAPI starts with creating an **app instance**. Think of it like starting a new project in any tool — you need a central object that everything else attaches to. In FastAPI, that object is your `app`. All your routes (endpoints), middleware (stuff that runs before/after requests), and configuration live on this one object. It's the heart of your API.

```python
from fastapi import FastAPI

app = FastAPI()
```

That's it — two lines and you have a FastAPI application. It doesn't do anything yet (no routes), but it's a valid, runnable app. The `app` variable name is important — when you start the server with Uvicorn, you'll tell it "go find the variable called `app` in this file." You *could* name it something else, but `app` is the universal convention. If you see any FastAPI tutorial or project, the main application object is called `app`.

---

### `Route Decorator` — Telling FastAPI About an Endpoint

A route is the connection between a URL path and a Python function. Your API might have dozens of endpoints — `/users`, `/bookmarks`, `/health` — and each one needs a function that handles it. But how does FastAPI know which function goes with which URL? That's what the **route decorator** does. It's the `@` line you put above a function that says "this function handles requests to *this* path using *this* HTTP method."

Without the decorator, your function is just a regular Python function sitting in a file doing nothing. The decorator is what registers it with FastAPI and makes it reachable from the outside world. You create routes using **decorators** — those `@` lines above a function.

```python
@app.get("/")
def root():
    return {"message": "hello world"}
```

Let's break this down piece by piece.

- `@app.get("/")` - `app` is your FastAPI object. When you did `app = FastAPI()`, that created an object with methods like `.get()`, `.post()`, `.put()`, `.delete()` built into it. So `app.get("/")` is calling the `.get()` method on your FastAPI object with the path `"/"`.

  This decorator says "when someone sends a **GET** request to the path `/` (the root URL), run the function below." There's also `@app.post()`, `@app.put()`, `@app.delete()` — one for each HTTP method you learned in Lesson 01.

- `def root():` - Just a regular Python function. The name doesn't matter to FastAPI (you could call it `banana` and it would work the same). But use descriptive names for your own sanity.

- `return {"message": "hello world"}` - You return a Python dictionary, and FastAPI automatically converts it to JSON and sends it back with a `200 OK` status code and `Content-Type: application/json` header. All that HTTP stuff from Lesson 01 — FastAPI handles it for you.

So when a client sends `GET /`, they get back:

```json
{"message": "hello world"}
```

---

### `@` — How Decorators Work Here

How does Python know that `@` does anything special? The `@` symbol is Python's **decorator syntax**. A decorator is a function that wraps another function to add behavior to it.

When Python sees this:

```python
@app.get("/")
def root():
    return {"message": "hello world"}
```

It's essentially doing this behind the scenes:

```python
def root():
    return {"message": "hello world"}

root = app.get("/")(root)
```

So `app.get("/")` takes your `root` function and **registers** it internally — "when a GET request comes in for `/`, call this function." Your function still exists, but now FastAPI knows about it and will call it when the right request arrives.

You don't need to understand the full mechanics of how decorators work internally right now. The mental model is: **`@app.get("/")` tells your FastAPI app "hook this function up to this path and method."**

---

### `Uvicorn` — Running the Server

Your FastAPI app is just Python code sitting in a file. To actually make it listen for HTTP requests, you need to run it with Uvicorn.

```
uvicorn src.main:app --reload
```

Let's break this command down:

- `uvicorn` — the server program
- `src.main:app` — tells Uvicorn where to find your app. This means "in the `src` folder, in the `main.py` file, the variable called `app`." The dot is a Python module path, the colon separates the file from the variable.
- `--reload` — this is a development flag that makes Uvicorn watch your files and automatically restart when you save changes. You'd never use this in production, but for development it's essential — you don't want to manually stop and restart the server every time you change a line of code.

Once it's running, you'll see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

That means your API is live at `http://127.0.0.1:8000`. You can open that in a browser or hit it with any HTTP client.

---

### `Swagger UI` — Free Interactive Docs

Here's one of the coolest things about FastAPI that most frameworks don't give you: **automatic API documentation**.

Once your server is running, go to:

- `http://127.0.0.1:8000/docs` — This opens **Swagger UI**, an interactive page where you can see all your endpoints, what they expect, and even test them by clicking "Try it out." You don't have to build this — FastAPI generates it from your code automatically.

- `http://127.0.0.1:8000/redoc` — An alternative documentation view called ReDoc. Same info, different layout. Some people prefer it.

This is huge for development. Instead of guessing what your API does or reading through code, you have a live, clickable interface that stays in sync with your actual code. As you add more routes, they automatically appear in the docs.

---

## Your Task

Here's what to do, step by step:

1. **Set up the project with Poetry.** If you haven't already initialized Poetry in this folder, do that first. Then activate the shell or use `poetry run` for commands.

2. **Install FastAPI and Uvicorn.** Use `poetry add` to install both packages. Check your `pyproject.toml` to confirm they're listed as dependencies.

3. **Create `src/main.py`.** Import FastAPI, create the app instance, and write a route that responds to `GET /` with a JSON message of your choice.

4. **Run the server.** Use `poetry run uvicorn src.main:app --reload` to start it. Make sure you run it from the project root (the `FastApiLearning` folder), not from inside `src/`. If you've activated the shell with `poetry shell`, you can just run `uvicorn src.main:app --reload` directly.

5. **Test it.** Open `http://127.0.0.1:8000` in your browser — you should see your JSON response. Then go to `http://127.0.0.1:8000/docs` and explore the Swagger UI. Try clicking "Try it out" on your endpoint.

6. **Add a couple more routes.** Try adding another `GET` endpoint at a different path. Maybe `/about` or `/health` or anything you want. Check that they show up in the Swagger docs.

When it's all working, let me know and I'll review your code. Next lesson we'll dig deeper into path parameters and query parameters.
