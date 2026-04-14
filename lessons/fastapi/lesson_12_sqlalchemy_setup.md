# Lesson 12: SQLAlchemy Setup

## What We're Doing
Installing SQLAlchemy, connecting your FastAPI app to a real database, and defining your first model — the Python class that represents a table.

## Why / Context

Up to now, every endpoint you've written has either returned hardcoded data or stored things in a Python dictionary that disappears the moment you restart the server. That's fine for learning route handlers and Pydantic models, but it's not an API — it's a memory-backed toy. Real APIs need *persistence*: data has to outlive the process, survive restarts, and be queryable across many requests from many users at once.

The traditional way to talk to a database from code is to write SQL strings by hand and send them over a connection. That works, but it has two big problems. First, you end up with SQL scattered through your codebase as string literals, which is hard to refactor and easy to get wrong. Second, and more dangerously, if you ever concatenate user input into those strings, you've invited SQL injection — the #1 classic API vulnerability, and something Lesson 18 will cover in detail.

The modern answer is an **ORM** — an Object-Relational Mapper. An ORM lets you describe your tables as Python classes and your rows as Python objects. When you want to insert a row, you create an instance of the class and hand it to the ORM. When you want to query, you write Python expressions and the ORM translates them into parameterized SQL (which is injection-safe by construction). The ORM we'll use is **SQLAlchemy** — the de facto standard in the Python world, and what most FastAPI projects build on.

SQLAlchemy is a big library. This lesson covers just the setup: getting a database running, connecting to it, defining a model, and creating the table. We won't insert or query anything yet — that's Lesson 13. Getting the plumbing right first makes the query work much less confusing.

## Concepts

### `Getting a Database Running` — Local Postgres with pgAdmin 4

SQLAlchemy is just a client library. It doesn't contain a database — it talks to one that's already running. So before anything else, you need a database process you can connect to.

You already have Postgres installed locally (you use it at work via pgAdmin 4), so you don't need to install anything new. You just need to: confirm the Postgres server is running, create a database for this project, and gather the connection details so SQLAlchemy can reach it.

#### Step 1: Confirm Postgres is running

When you installed Postgres, it set itself up as a Windows service that starts automatically. To confirm it's running, open `services.msc` (Win+R → type `services.msc`) and look for an entry like `postgresql-x64-16` (the version number depends on what you installed). Status should be "Running." If it isn't, right-click and choose Start.

You can also just open pgAdmin 4 — if it connects to your local server without an error, the service is up.

#### Step 2: Create a database for this project

Open pgAdmin 4. In the left sidebar, expand your server (usually named "PostgreSQL 16" or similar), right-click on **Databases**, and choose **Create → Database…**. Name it something like `fastapi_learning` and click Save. That's it — you now have an empty database ready to use.

#### Step 3: Build your connection URL

SQLAlchemy needs a connection string in this format:

```
postgresql+psycopg://USERNAME:PASSWORD@HOST:PORT/DATABASE
```

For your local install, the values are:
- `USERNAME` - usually `postgres` (the default superuser created during install)
- `PASSWORD` - whatever you set during install (the one you type into pgAdmin)
- `HOST` - `localhost`
- `PORT` - `5432` (the Postgres default — unless you changed it during install)
- `DATABASE` - `fastapi_learning` (the one you just created)

So your final URL looks something like:

```
postgresql+psycopg://postgres:yourpassword@localhost:5432/fastapi_learning
```

The `postgresql+psycopg://` part is SQLAlchemy syntax — the `+psycopg` names the driver library to use (we'll install it in a minute).

This URL contains your password, which is exactly why Lesson 11 set up `.env` files. You'll put this string in `.env` (which is gitignored), not in your code.

**Try it:** Open pgAdmin 4, confirm you can connect, create a `fastapi_learning` database, and write down your connection URL somewhere temporary. You'll put it in `.env` in the task at the end.

---

### `Installing SQLAlchemy and a Driver`

SQLAlchemy itself is one package, but it needs a *driver* — the low-level library that actually speaks the database's wire protocol. For Postgres, the modern driver is **psycopg** (version 3).

```bash
poetry add sqlalchemy psycopg[binary]
```

The `[binary]` suffix on psycopg tells Poetry to install the pre-built binary version, which avoids needing a C compiler on your machine. It's what you want for local development.

**Try it:** Run the command above to install both packages.

---

### `The Engine` — The Connection Pool

SQLAlchemy has two main pieces: the **engine** and the **session**. Understanding the difference up front saves a lot of confusion later.

The **engine** is a long-lived object that represents the connection to your database. It's created once when your app starts and lives for the entire lifetime of the process. Under the hood, it manages a pool of real database connections — opening new ones when traffic is high, reusing existing ones when traffic is low, and closing idle ones after a while. You don't use the engine directly in your route handlers; you create it once and hand it off to the session maker.

```python
# src/database.py
from sqlalchemy import create_engine
from src.config import settings

engine = create_engine(settings.database_url)
```

`create_engine` doesn't actually open a connection right away — it just builds the engine object. The first real connection is opened lazily, the first time something asks for one. This is why a typo in your connection string won't fail at import time; it'll fail at the first query.

Notice where the URL comes from: `settings.database_url`. This is the payoff from Lesson 11 — instead of hardcoding the connection string, you read it from your settings, which reads it from `.env`. You'll add a `database_url` field to your `Settings` class in the task at the end.

---

### `The Session` — Your Unit of Work

A **session** is a short-lived object you use to interact with the database for a single logical operation — typically one HTTP request. Sessions track which objects you've loaded, which ones you've modified, and which ones you want to insert. When you call `session.commit()`, everything you've done through that session is sent to the database as a single transaction. When you call `session.close()`, the session is discarded.

You don't create sessions directly. You create a *session factory* — a function that produces new sessions — and use it to hand out fresh sessions per request:

```python
# src/database.py
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
```

`sessionmaker` returns a class (by convention named `SessionLocal`) that you can call like a constructor — `SessionLocal()` gives you a new session instance. The two flags deserve a quick note:

#### Parameters:
- `autoflush=False` - don't automatically send pending changes to the database before every query. You want to decide when writes happen explicitly. Without this, subtle bugs appear where a read triggers a partial write of an object that's not ready yet.
- `autocommit=False` - every session starts in a transaction. Nothing is written until you call `.commit()`. This is the safe default — if your code raises halfway through a series of changes, the whole thing rolls back.

You'll use `SessionLocal` inside a FastAPI dependency in Lesson 13, so every route handler gets its own fresh session that automatically closes when the request finishes. For now, just creating the factory is enough.

---

### `DeclarativeBase` — The Base Class for Models

SQLAlchemy models are Python classes that inherit from a shared base class. That base class is what links your model definitions to the metadata SQLAlchemy needs to generate SQL. In SQLAlchemy 2.0, you create it by subclassing `DeclarativeBase`:

```python
# src/database.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

Every model you define will inherit from `Base`. All models that share the same `Base` share the same metadata registry, which is how SQLAlchemy knows about all your tables as a group — useful when you later say "create every table at once" or "generate a migration for everything that changed."

You only need one `Base` for your whole app. Define it in one place and import it wherever you define models.

---

### `Defining a Model` — From Python Class to SQL Table

Now the actual fun part. Here's a minimal model:

```python
# src/models/card.py
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.database import Base

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cost: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500))
```

There's a lot going on in a small amount of code. Let me break it down.

#### Parts:
- `class Card(Base)` - inherits from the `Base` you defined above, registering this model with SQLAlchemy's metadata.
- `__tablename__ = "cards"` - the actual SQL table name. By convention, class names are singular (`Card`) and table names are plural (`cards`).
- `Mapped[int]` - this is SQLAlchemy's typed-column annotation. It tells both Python's type checker and SQLAlchemy itself that this attribute holds an `int`. If you later write `card.cost = "free"`, your editor will flag it.
- `mapped_column(Integer, primary_key=True)` - the column definition. The first argument is the SQL type (`Integer`, `String(100)`, etc.), and the keyword arguments configure constraints (`primary_key`, `nullable`, `unique`, `default`, and so on).

Note the two layers of types here: `Mapped[int]` is the *Python* type (what your code sees), and `Integer` is the *SQL* type (what the database sees). They usually line up, but not always — a `Mapped[str]` might be backed by `String(100)` or `Text` depending on whether you want a length limit.

The pattern of one model per file in a `models/` package is what the learning path set up back in Lesson 08. You'll create `src/models/` and put each model class in its own file, re-exporting them from `src/models/__init__.py` so other code can import them cleanly.

**Try it:** Pick a domain you care about — Slay the Spire cards, books, recipes, whatever — and sketch out a single model class. Give it an `id` primary key plus three or four simple columns. Don't worry about relationships or foreign keys yet; one table is enough for now.

---

### `Creating the Tables` — `Base.metadata.create_all()`

Defining a model class doesn't create a table in the database. The class is just a description — the actual `CREATE TABLE` statement has to be sent to the database at some point. The quick-and-dirty way to do that is:

```python
Base.metadata.create_all(bind=engine)
```

When you call this, SQLAlchemy looks at every model registered on `Base`, generates the matching `CREATE TABLE` statements, and runs them. If a table already exists, `create_all` skips it — it won't alter existing tables or drop columns. This is helpful for getting started but it's also its biggest limitation: once the table exists, `create_all` can't evolve it. If you add a new column to your model, `create_all` will *not* add it to the database.

That limitation is exactly why Lesson 14 introduces **Alembic**, which handles schema changes properly with versioned migration scripts. For now, `create_all` is fine — you're just bootstrapping an empty database.

One important detail: `create_all` only sees models that have been *imported* before you call it. If your `Card` class lives in `src/models/card.py` and nobody has imported it yet, SQLAlchemy doesn't know it exists. The usual fix is to import all your models in `src/models/__init__.py` so that `from src import models` is enough to register them.

Where do you actually call `create_all`? A common pattern is to run it once at app startup:

```python
# src/main.py
from src.database import Base, engine
from src import models  # noqa: F401 — ensures models are registered

Base.metadata.create_all(bind=engine)
```

The `# noqa: F401` comment tells your linter "yes, I know this import looks unused — it's intentional." Importing the package has the side effect of registering the models, even though you don't reference `models` by name afterward.

**Try it:** Wire up `create_all` in `main.py`, start the server, and verify the table got created. In pgAdmin 4, expand your server → Databases → `fastapi_learning` → Schemas → public → Tables, and refresh. You should see your new table listed. Right-click it and choose "View/Edit Data → All Rows" to confirm it's there (it'll be empty).

---

## Your Task

1. Open pgAdmin 4 and create a new database called `fastapi_learning` on your local Postgres server.
2. Install SQLAlchemy and the `psycopg[binary]` driver with Poetry.
3. Add a `database_url: str` field to your `Settings` class in `src/config.py`. Don't give it a default — you want a validation error at startup if it's missing.
4. Add `DATABASE_URL` to your `.env` file with the actual connection string (`postgresql+psycopg://postgres:yourpassword@localhost:5432/fastapi_learning`), and add a placeholder line to `.env.example`.
5. Create `src/database.py` containing the `engine`, the `SessionLocal` factory, and the `Base` class.
6. Create `src/models/` as a package with an `__init__.py`.
7. Define one model class in its own file under `src/models/` — pick a domain you enjoy and give it a primary key plus a few columns.
8. Re-export your model from `src/models/__init__.py` so it gets registered on `Base`.
9. In `src/main.py`, import `src.models` and call `Base.metadata.create_all(bind=engine)` so the table is created when the app starts.
10. Run the server, then refresh the Tables list in pgAdmin 4 to confirm your new table appears.
