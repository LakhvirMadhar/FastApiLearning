# Paths vs Path Parameters vs Query Parameters

## The Three Things

These three concepts all involve URLs, but they do different jobs:

| Term | Example | What it does |
|------|---------|-------------|
| **Path** (endpoint) | `/cards` | The URL structure. Determines which function runs. |
| **Path parameter** | `{card_id}` in `/cards/{card_id}` | A variable piece of the path. Identifies a specific resource. |
| **Query parameter** | `?skip=0&limit=10` | Key-value pairs after the `?`. Filters or modifies the request. |

## Path

A path is the fixed part of the URL that routes the request to a function. It's also called an endpoint or a route.

```python
@router.get("/cards")
def get_cards():
    ...
```

`/cards` is a path. It's a literal, fixed string. There's no variable in it. When someone hits `GET /cards`, FastAPI matches this route and calls `get_cards()`.

Other examples of paths:
- `/` — the root
- `/about` — the about page
- `/cards/featured` — a specific, literal path (no variables)
- `/neow/blessings` — another literal path

A path by itself is **not** a path parameter. There's no `{placeholder}` in it.

## Path Parameter

A path parameter is a variable segment inside the path. You declare it with curly braces `{}` in the route decorator, and FastAPI extracts the value from the URL.

```python
@router.get("/cards/{card_id}")
def get_card(card_id: str):
    ...
```

When someone hits `GET /cards/42`, FastAPI matches this route and sets `card_id = "42"`. The `{card_id}` part is the path parameter — it's a placeholder that matches any value at that position in the URL.

Path parameters identify **which** resource you want:
- `/cards/1` — card with ID 1
- `/cards/99` — card with ID 99
- `/characters/Ironclad` — the character named Ironclad

How FastAPI knows something is a path parameter: the variable name appears in both the path string (`"/cards/{card_id}"`) and the function signature (`card_id: str`). If it's in the path, it's a path parameter.

## Query Parameter

A query parameter is a key-value pair that comes after `?` in the URL. It's not part of the path — it's additional data tacked onto the end.

```python
@router.get("/cards")
def get_cards(skip: int = 0, limit: int = 10):
    ...
```

When someone hits `GET /cards?skip=5&limit=20`, FastAPI matches the path `/cards`, then extracts `skip=5` and `limit=20` from the query string and passes them to the function.

Query parameters filter or modify **how** you get the resource:
- `/cards?skip=0&limit=10` — get cards, starting from 0, max 10
- `/cards?skip=10&limit=10` — get cards, starting from 10, max 10
- `/characters/Ironclad/cards?card_type=attack` — get Ironclad's cards, but only attacks

How FastAPI knows something is a query parameter: the variable name appears in the function signature but **not** in the path string. If it's in the function but not the path, it's a query parameter.

## How FastAPI Decides

FastAPI uses one simple rule to distinguish path parameters from query parameters:

1. Look at the function parameter name.
2. Is it in the path string (inside `{}`)? → **path parameter**
3. Is it NOT in the path string? → **query parameter**

```python
@router.get("/characters/{character_name}/cards")
def get_character_cards(character_name: str, card_type: str | None = None, energy: int | None = None):
    ...
```

- `character_name` → appears in the path as `{character_name}` → **path parameter**
- `card_type` → not in the path → **query parameter**
- `energy` → not in the path → **query parameter**

A request to this endpoint looks like: `GET /characters/Ironclad/cards?card_type=attack&energy=1`

- Path: `/characters/Ironclad/cards`
- Path parameter: `character_name = "Ironclad"`
- Query parameters: `card_type = "attack"`, `energy = 1`

## Defaults and Required vs Optional

**Path parameters are always required.** You can't hit `/cards/` without providing a card ID — the URL would be `/cards/` which is a different path entirely.

**Query parameters can be optional or required**, depending on whether they have a default value:

```python
# skip and limit are optional (have defaults)
def get_cards(skip: int = 0, limit: int = 10):

# card_type is required (no default)
def get_cards(card_type: str):
```

If `card_type` has no default, the client must provide it: `/cards?card_type=attack`. If they don't, FastAPI returns a 422 validation error.

## The Full Picture

Here's a complete URL broken into its parts:

```
GET /characters/Ironclad/cards?card_type=attack&energy=1
    |_________________________| |_________________________|
              path                    query string

    /characters/{character_name}/cards
                 |_____________|
                 path parameter

                                 ?card_type=attack&energy=1
                                  |_____________| |_______|
                                  query param 1   query param 2
```

- The **path** determines which function runs.
- **Path parameters** are variables embedded in the path that identify the specific resource.
- **Query parameters** are optional (or required) modifiers that come after `?` and filter/adjust the response.

## Why This Matters

Understanding the difference between these three things isn't just vocabulary — it affects how you design your API and how other developers (and frontends) use it.

**Consistent API design.** If you mix up when to use path params vs query params, your API becomes unpredictable. Imagine some endpoints use `/cards/attack` to filter by type, and others use `/cards?type=attack`. A frontend developer consuming your API has to memorize which pattern each endpoint uses instead of relying on a consistent convention. The standard: path parameters for identity ("which thing"), query parameters for filtering ("how to get it").

**Route conflicts.** As covered in the Q4 deep dive, path parameters create wildcard patterns that can swallow literal routes. If you don't understand the distinction between a path (`/cards/featured`) and a path parameter (`/cards/{card_id}`), you'll accidentally create unreachable routes and spend hours debugging silent failures.

**Documentation and discoverability.** FastAPI generates Swagger docs from your route definitions. Path parameters show up as required fields in the URL. Query parameters show up as optional filter controls. If you put filtering logic in path parameters instead of query parameters, Swagger becomes confusing — users can't tell what's required for identity vs what's optional for filtering.

**Frontend integration.** When a React or mobile app calls your API, the developer building that frontend needs to construct URLs. Clear conventions make this easy:
- To get one card: `fetch(\`/cards/${cardId}\`)` — path parameter, always needed
- To filter the list: `fetch(\`/cards?skip=${page * 10}&limit=10\`)` — query parameters, optional

If you used path parameters for everything (`/cards/skip/0/limit/10`), the frontend code becomes brittle and ugly, and adding a new filter means changing the URL structure instead of just appending another `&key=value`.

**Interview signal.** Knowing when to use path vs query parameters — and being able to articulate why — is a common backend interview question. "Design the endpoints for a bookstore API" is a classic prompt. If you use path parameters for identity and query parameters for filtering without being told, the interviewer knows you understand REST conventions.

## TL;DR

- **Path** = the URL route (`/cards`). Not a parameter. Just tells FastAPI which function to call.
- **Path parameter** = `{variable}` inside the path (`/cards/{card_id}`). Identifies which resource. Always required.
- **Query parameter** = `?key=value` after the path (`/cards?skip=0`). Filters or modifies the request. Can be optional.
- FastAPI decides which is which by checking if the variable name appears in the path string or not.
- **Why it matters:** consistent API design, avoiding route conflicts, clean Swagger docs, easy frontend integration, and interview readiness.
