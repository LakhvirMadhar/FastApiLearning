# Lesson 11: `pydantic-settings` and `.env` Files

## What We're Doing
Managing configuration — database URLs, secret keys, API tokens — outside of your code using environment variables and `.env` files.

## Why / Context

Right now, if you needed a database URL, you'd probably hardcode it somewhere in your code:

```python
DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"
```

This is a problem for several reasons. First, you'd commit your password to git — anyone with access to the repo sees it. Second, your local database URL is different from the production one. You'd have to change the code every time you deploy. Third, if you ever rotate a password or API key, you have to find every place it's used in the code and update it.

The solution is environment variables. Instead of putting values in your code, you put them in the environment (or a `.env` file), and your code reads them at startup. The code never contains the actual values — just the *names* of the variables to look up.

FastAPI's ecosystem uses `pydantic-settings` for this. It gives you a typed, validated settings object that reads from environment variables and `.env` files automatically. Same Pydantic validation you already know, applied to configuration.

## Concepts

### `Environment Variables` — The Foundation

Before touching any library, you should understand what environment variables are. They're key-value pairs that exist in your operating system's environment — outside your code. Every process on your machine has access to them.

You can set one in your terminal:

```bash
# Linux/Mac
export DATABASE_URL="postgresql://user:password@localhost:5432/mydb"

# Windows PowerShell
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/mydb"
```

And read it in Python:

```python
import os
database_url = os.getenv("DATABASE_URL")
```

This works, but it has no validation. If `DATABASE_URL` isn't set, you get `None` and your app crashes somewhere downstream with a confusing error. If someone sets it to `"not-a-url"`, you won't know until the database connection fails. `pydantic-settings` fixes this by validating environment variables the same way Pydantic validates request bodies.

**Try it:** Open a Python shell and run `import os; print(os.environ)` to see all the environment variables currently set on your machine. You'll see things like `PATH`, `HOME`/`USERPROFILE`, and others that your OS and tools set. These are the same kind of variables your app will read from.

---

### `pydantic-settings` — Typed Configuration

First, install it:

```bash
poetry add pydantic-settings
```

Then create a settings class. It works just like a Pydantic model, but inherits from `BaseSettings` instead of `BaseModel`:

```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "My FastAPI App"
    debug: bool = False
```

This is all you need to start with. Fields without defaults are required — pydantic-settings will raise a validation error at startup if the environment variable isn't set. Both fields here have defaults, so they're optional — if the environment variable isn't set, the default is used.

When you create an instance of `Settings()`, pydantic-settings does the following:

1. Looks for environment variables matching each field name (case-insensitive)
2. `app_name` → looks for `APP_NAME` in the environment
3. `debug` → looks for `DEBUG` in the environment
4. If a field has a default (like both of ours do), the environment variable is optional
5. If a field has no default, pydantic-settings raises a validation error if the variable isn't set

The field names in your class map to environment variable names automatically — `app_name` matches `APP_NAME`. Pydantic-settings handles the case conversion.

```python
settings = Settings()
print(settings.app_name)  # reads from APP_NAME env var, or defaults to "My FastAPI App"
print(settings.debug)     # reads from DEBUG env var, or defaults to False
```

You get the same type validation as regular Pydantic. If `DEBUG` is set to `"yes"`, pydantic-settings will try to coerce it to a `bool`. If you later add a required field like `database_url: str` without a default and it's missing from the environment, you get a clear validation error at startup — not a random crash later.

Later, when you add a database and authentication, you'll add fields like `database_url: str` and `secret_key: SecretStr`. `SecretStr` is a Pydantic type (from `pydantic import SecretStr`) designed for sensitive values. If you ever print the settings object or it ends up in a log, a `SecretStr` field shows as `SecretStr('**********')` instead of the actual value. To get the real value in your code, you call `settings.secret_key.get_secret_value()`. This is a simple guard against accidentally leaking secrets in logs or error messages — and exactly the kind of thing the OWASP lesson (Lesson 18) will cover in more depth.

**Try it:** Create `src/config.py` with a `Settings` class that has `app_name` (with a default) and `debug` (defaulting to `False`). Don't add `database_url` yet — we'll add that when we get to the database lessons. Create an instance and print the values.

---

### `.env` Files — Configuration on Disk

Setting environment variables in your terminal works, but they disappear when you close the terminal. For local development, you want a file that holds your configuration. That's what `.env` files are — a simple text file with one `KEY=VALUE` per line:

```
# .env
APP_NAME=Slay the Spire API
DEBUG=true
```

To make pydantic-settings read from a `.env` file, add a `model_config` to your settings class:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "My FastAPI App"
    debug: bool = False
```

`SettingsConfigDict(env_file=".env")` tells pydantic-settings to look for a `.env` file in the current working directory (where you run uvicorn from). If both an environment variable and a `.env` entry exist for the same key, the environment variable wins. This is useful — your `.env` file has local defaults, but you can override them in production by setting real environment variables.

One critical rule: **never commit `.env` to git.** It contains secrets. Even though your current `.env` only has `APP_NAME` and `DEBUG`, you'll add database URLs and secret keys later — and you don't want to get into the habit of committing this file. Add it to `.gitignore` immediately. Instead, create a `.env.example` file (which you *do* commit) that shows the required variables without real values:

```
# .env.example
APP_NAME=My FastAPI App
DEBUG=false
```

When a new developer clones the repo, they copy `.env.example` to `.env` and fill in their own values. Later, when you add database and auth fields, you'll add them to `.env.example` too:

```
# .env.example (later, when you add database + auth)
APP_NAME=My FastAPI App
DEBUG=false
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=change-me
```

**Try it:** Create a `.env` file in your project root with `APP_NAME` and `DEBUG`. Add `.env` to your `.gitignore` (create the file if you don't have one). Update your `Settings` class to use `SettingsConfigDict(env_file=".env")`. Create a `.env.example` with placeholder values.

---

### `Using Settings in Your App` — Connecting It All

Once you have a `Settings` class, you need to make it available to your routes. There are two common approaches.

**Approach 1: Create a single instance and import it.**

```python
# src/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "My FastAPI App"
    debug: bool = False

settings = Settings()
```

```python
# src/routers/cards.py
from src.config import settings

@router.get("/info")
def app_info():
    return {"app_name": settings.app_name, "debug": settings.debug}
```

Simple and direct. The settings are created once when the module is imported, and every file that needs them just imports the `settings` instance.

**Approach 2: Use a dependency.**

```python
# src/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "My FastAPI App"
    debug: bool = False

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

```python
# src/routers/cards.py
from fastapi import Depends
from src.config import Settings, get_settings

@router.get("/info")
def app_info(settings: Settings = Depends(get_settings)):
    return {"app_name": settings.app_name, "debug": settings.debug}
```

The `@lru_cache` decorator means `get_settings()` only creates the `Settings` object once — after that, it returns the cached instance. This avoids reading the `.env` file on every request.

The dependency approach is more testable — in tests, you can override `get_settings` to return fake settings without needing a real `.env` file. For now, approach 1 is simpler. You'll appreciate approach 2 when you get to the testing lesson.

**Try it:** Use approach 1 — create a `settings` instance in `config.py` and import it in `main.py`. Use `settings.app_name` in your root route's response instead of a hardcoded string. Verify it works by changing the value in `.env` and restarting the server.

---

### `Nested and Complex Settings` — Grouping Related Config

As your app grows, you might want to organize settings into groups:

```python
class DatabaseSettings(BaseSettings):
    url: str
    pool_size: int = 5
    echo: bool = False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_nested_delimiter="__")

    app_name: str = "My FastAPI App"
    debug: bool = False
    database: DatabaseSettings
```

With `env_nested_delimiter="__"`, pydantic-settings maps nested fields using double underscores:

```
# .env
APP_NAME=Slay the Spire API
DATABASE__URL=postgresql://user:password@localhost:5432/spire
DATABASE__POOL_SIZE=10
```

`DATABASE__URL` maps to `settings.database.url`. This keeps related configuration grouped together in both the code and the `.env` file.

You won't need this right now, but it's good to know it exists for when your configuration grows.

---

## Your Task

1. Install `pydantic-settings` with `poetry add pydantic-settings`
2. Create `src/config.py` with a `Settings` class — include `app_name` (with a default) and `debug` (defaulting to `False`)
3. Create a `.env` file in the project root with values for `APP_NAME` and `DEBUG`
4. Add `.env` to `.gitignore`
5. Create a `.env.example` with placeholder values
6. Add `SettingsConfigDict(env_file=".env")` to your `Settings` class
7. Import the settings in `main.py` and use `settings.app_name` in your root route's response
8. Restart the server, change a value in `.env`, restart again, and confirm the new value shows up
