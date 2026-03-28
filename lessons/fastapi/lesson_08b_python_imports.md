# Lesson 08b: Python Imports and `__init__.py`

## What We're Doing
Understanding how Python finds and loads code from other files — so imports stop feeling like guesswork.

## Why / Context

Every time you split code across files, you need imports. And every time imports break, the error messages are cryptic: `ModuleNotFoundError: No module named 'schemas'`. You stare at the folder, the file is *right there*, and Python can't find it. The problem is almost always the same thing: you don't understand where Python is looking.

This isn't a FastAPI concept — it's a Python fundamental that trips up everyone. Once it clicks, you'll never struggle with it again.

## Concepts

### `Modules and Packages` — The Two Building Blocks

A **module** is just a `.py` file. When you write `cards.py`, that's a module called `cards`.

A **package** is a folder that contains an `__init__.py` file. The `__init__.py` is what tells Python "this folder is importable, not just a regular directory." It can be completely empty — its existence is what matters.

```
src/
├── main.py              <-- module: "main"
├── routers/             <-- package: "routers" (because it has __init__.py)
│   ├── __init__.py
│   └── cards.py         <-- module: "routers.cards"
└── schemas/             <-- package: "schemas" (because it has __init__.py)
    ├── __init__.py
    └── cards.py         <-- module: "schemas.cards"
```

Without `__init__.py`, Python treats the folder as just a folder. You can't import from it at all. With `__init__.py`, the folder becomes a package and everything inside it becomes importable.

**Try it:** Delete the `__init__.py` from your `routers/` folder temporarily, then try running the server. You'll see the import fail. Put it back and it works again. That's the only thing `__init__.py` does at a minimum — it marks the folder as a package.

---

### `sys.path` — Where Python Looks

When you write `from src.schemas.cards import Card`, Python doesn't search your entire hard drive. It has a specific list of directories it checks, called `sys.path`. You can see it yourself:

```python
import sys
print(sys.path)
```

The most important entry in `sys.path` is the **directory where you ran the command from**. When you run:

```bash
uvicorn src.main:app --reload
```

from `FastApiLearning/`, Python adds `FastApiLearning/` to `sys.path`. That becomes the root for all your imports. Every import path you write is relative to that root.

This is why the same import can work or break depending on where you open your terminal:

```bash
# From FastApiLearning/ (project root):
uvicorn src.main:app --reload
# Python root = FastApiLearning/
# Import: from src.schemas.cards import Card  ✓
# Import: from schemas.cards import Card      ✗ (no schemas/ in FastApiLearning/)

# From FastApiLearning/src/:
uvicorn main:app --reload
# Python root = FastApiLearning/src/
# Import: from schemas.cards import Card      ✓ (schemas/ is in src/)
# Import: from src.schemas.cards import Card  ✗ (no src/ inside src/)
```

Same code, same files, different results — all because of where you ran the command. This is the #1 reason imports confuse people. The fix is simple: always run from the same place, and write your imports to match.

Since you run `uvicorn src.main:app` from the project root, all your imports start with `src.`:

```python
from src.schemas.cards import Card        # ✓
from src.routers.cards import router      # ✓
```

**Try it:** Open a Python shell from your project root and run `import sys; print(sys.path)`. Find the entry that matches your project root. That's where Python starts looking.

---

### `__init__.py` as a Shortcut — Re-exporting

So far `__init__.py` has just been an empty file that marks a folder as a package. But it can also contain code, and the most common use is **re-exporting** — importing things inside `__init__.py` so they're available directly from the package name.

Without re-exporting, you have to know exactly which file each model lives in:

```python
from src.schemas.cards import Card, CardType, CardResponse
from src.schemas.neow import BlessingResponse
from src.schemas.characters import Character, CharacterResponse
```

That works, but it means every file that needs `Card` has to know it lives in `schemas.cards` specifically. If you later move `Card` to a different file, every import breaks.

With re-exporting in `__init__.py`:

```python
# src/schemas/__init__.py
from src.schemas.cards import Card, CardType, CardResponse
from src.schemas.neow import BlessingResponse
from src.schemas.characters import Character, CharacterResponse
```

Now other files can import directly from the package:

```python
from src.schemas import Card, CardType, CardResponse
```

Shorter, and the caller doesn't need to know which file `Card` lives in. The `__init__.py` acts as the package's "public interface" — it decides what's available when someone imports from the package.

This is the same pattern you've already been using without realizing it. When you write `from fastapi import FastAPI`, you're not importing from a single file — `fastapi` is a package, and its `__init__.py` re-exports `FastAPI` so you don't have to write `from fastapi.applications import FastAPI` (which is where the class actually lives).

**Try it:** Add re-exports to `src/schemas/__init__.py`. Then update your router files to import from `src.schemas` instead of `src.schemas.cards`. Both ways work — the `__init__.py` version is just cleaner.

---

### `What Goes in __init__.py` — Guidelines

Not everything needs to be re-exported. A good rule of thumb:

- **Re-export things other files need to import** — models, schemas, shared utilities. These are the "public" parts of your package.
- **Don't re-export internal helpers** — if a function is only used inside one file in the package, leave it there. Not everything needs to be in `__init__.py`.
- **Keep it simple** — `__init__.py` should be mostly import statements. Don't put logic or class definitions in here. If you open `__init__.py` and see anything other than imports, something is probably in the wrong place.

For your schemas package, the `__init__.py` is straightforward — just re-export all your Pydantic models. For your routers package, you probably don't need re-exports at all, since `main.py` imports each router individually and that's fine.

---

### `Import Styles` — Which One to Use

Python has two import styles, and you'll see both in the wild:

**Absolute imports** start from the root of your project:

```python
from src.schemas.cards import Card
```

**Relative imports** use dots to mean "from the current package":

```python
# Inside src/routers/cards.py
from ..schemas.cards import Card
# ..  = go up one level (from routers/ to src/)
# .schemas.cards = then go into schemas/cards.py
```

Single dot (`.`) means "this package." Double dot (`..`) means "parent package." Triple dot (`...`) means "grandparent," and so on.

Relative imports have one benefit: they don't depend on the project root name. If you rename `src/` to `app/`, relative imports still work. But they're harder to read — `from ..schemas.cards import Card` forces you to mentally count dots and figure out where you are in the folder tree.

**For this project, stick with absolute imports** (`from src.schemas.cards import Card`). They're explicit, readable, and you always know exactly what file you're importing from. Most FastAPI projects use absolute imports.

---

## Your Task

1. Add re-exports to `src/schemas/__init__.py` — import all your Pydantic models there
2. Update `src/routers/cards.py` to import schemas from `src.schemas` (using the `__init__.py` shortcut)
3. Update `src/routers/characters.py` the same way
4. Update `src/routers/neow.py` the same way
5. Run the server and verify everything still works
