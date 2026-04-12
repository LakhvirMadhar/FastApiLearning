# Pydantic: The Proper Explanation

## The Short Version

If you walked away from Lesson 05 thinking "Pydantic is a validation library," that's accurate but massively underselling it. Pydantic is better described as a **data modeling library** — a tool for defining the shape of data in your program and then doing every useful thing you can do with a shape: parse it, validate it, serialize it, document it, transform it, and enforce it at runtime.

Validation is just the part you notice first because it's the part that yells at you when something goes wrong. The quieter parts — parsing, serialization, schema generation — are actually doing the most work in a typical FastAPI app. You just don't see them because they succeed silently.

This doc walks through what Pydantic actually does, and why it's the secret ingredient that makes FastAPI feel so much nicer than older Python web frameworks.

## The Big Picture: What Pydantic Actually Does

A Pydantic model is a Python class that inherits from `BaseModel` and uses type hints to describe fields. Once you have that class, Pydantic gives you five distinct capabilities, all from the same definition:

1. **Parsing** - take messy input (a dict, a JSON string, environment variables) and turn it into a clean, typed Python object.
2. **Validation** - reject input that doesn't fit the shape, with clear error messages pointing to exactly what's wrong.
3. **Serialization** - take a typed Python object and turn it *back* into a dict or JSON string, with control over how that export looks.
4. **Schema generation** - emit a JSON Schema document describing the model, which downstream tools (like FastAPI's auto-generated docs) can consume.
5. **A single source of truth** - the same model drives all four of the above, so your validation rules, your API docs, and your serialization format never drift out of sync.

That last one is the real superpower. In most languages and frameworks, you write your validation logic in one place, your API docs in another, your serialization code in a third, and your type definitions in a fourth — and they slowly rot out of agreement. Pydantic collapses them into one class.

Keep those five jobs in mind as you read the rest of this doc. Every feature below is just an expansion of one of them.

---

## Concepts

### `Parsing` — The First Thing Pydantic Does

Most people think validation happens first, but it doesn't. Parsing happens first. Consider:

```python
from pydantic import BaseModel

class Card(BaseModel):
    name: str
    cost: int

card = Card(name="Strike", cost="1")  # note: "1" is a string!
print(card.cost)  # 1 — an actual int
print(type(card.cost))  # <class 'int'>
```

You passed in the string `"1"`, but `card.cost` came out as the integer `1`. Pydantic didn't reject the input — it *coerced* it. That's parsing. By default, Pydantic operates in what's called **lax mode**: if it can reasonably convert a value to the declared type, it will. `"1"` becomes `1`, `"true"` becomes `True`, `"2024-01-15"` becomes a `datetime.date`, and so on.

This sounds like a small thing but it's why Pydantic composes so well with the outside world. HTTP request bodies come in as JSON, which has limited types. Environment variables come in as strings, always. Database rows come in as tuples or dicts. Pydantic's job is to absorb that messy reality and hand your business logic a clean, typed object that obeys your declared shape.

If you *don't* want coercion and you'd rather reject `"1"` when you asked for an int, you can opt into **strict mode** either per-field or for the whole model:

```python
from pydantic import BaseModel, ConfigDict

class Card(BaseModel):
    model_config = ConfigDict(strict=True)
    name: str
    cost: int

Card(name="Strike", cost="1")  # now raises ValidationError
```

The mental model: **parsing converts, validation enforces.** Lax mode is forgiving at the conversion step. Strict mode turns that forgiveness off.

---

### `Field Constraints` — Validation Beyond Types

Type hints alone say "this should be an int." But sometimes you need to say "this should be an int between 0 and 10, and it can't be negative." That's what `Field` is for.

```python
from pydantic import BaseModel, Field

class Card(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    cost: int = Field(ge=0, le=10)
    description: str = Field(default="", max_length=500)
```

#### Common constraints:
- `ge`, `le`, `gt`, `lt` - greater/less than (or equal to) for numbers
- `min_length`, `max_length` - for strings, lists, dicts
- `pattern` - regex pattern for strings
- `multiple_of` - number must be a multiple of this
- `default` - default value if the field isn't provided
- `default_factory` - for mutable defaults, pass a callable like `default_factory=list`

The nice part is these constraints show up in the generated JSON Schema, which means they show up in FastAPI's `/docs` page too. Your API consumers see the rules without you writing them a README.

---

### `field_validator` and `model_validator` — Custom Logic

When the built-in constraints aren't enough, you can write your own validation logic using decorators.

`@field_validator` runs custom logic on a single field. It's a classmethod that receives the value and returns it (possibly transformed):

```python
from pydantic import BaseModel, field_validator

class Card(BaseModel):
    name: str
    cost: int

    @field_validator("name")
    @classmethod
    def name_must_be_titlecase(cls, v: str) -> str:
        if v != v.title():
            raise ValueError("name must be in Title Case")
        return v
```

If the validator returns a value, that's what gets stored. If it raises `ValueError`, Pydantic wraps it in a `ValidationError` with the field name attached. You can also transform the value inside the validator — a classic use is stripping whitespace, lowercasing emails, or normalizing formatting.

`@model_validator` runs *after* all the fields have been parsed and validated individually, giving you access to the whole model at once. This is how you enforce rules that depend on multiple fields:

```python
from pydantic import BaseModel, model_validator

class DateRange(BaseModel):
    start: int
    end: int

    @model_validator(mode="after")
    def end_must_be_after_start(self):
        if self.end < self.start:
            raise ValueError("end must be >= start")
        return self
```

The `mode="after"` bit is important. Model validators have two modes:
- `mode="before"` - runs on the raw input *before* field-level parsing. You get a dict, and you can transform/clean it before Pydantic tries to coerce anything.
- `mode="after"` - runs on the constructed model instance *after* all field validation has succeeded. This is the common case.

---

### `Serialization` — The Other Direction

So far every example has been input → model. But models also go the other way, and this is where people often don't realize Pydantic is doing work for them.

```python
card = Card(name="Strike", cost=1, description="Deal 6 damage.")

card.model_dump()
# {'name': 'Strike', 'cost': 1, 'description': 'Deal 6 damage.'}

card.model_dump_json()
# '{"name":"Strike","cost":1,"description":"Deal 6 damage."}'
```

`.model_dump()` returns a plain Python dict. `.model_dump_json()` returns a JSON string directly. FastAPI calls one of these on every response that uses a Pydantic model — you never wrote `json.dumps` yourself because Pydantic did it for you.

Serialization is more configurable than it looks. Some options you'll reach for:

#### Parameters:
- `exclude={"password"}` - drop certain fields from the output
- `exclude_none=True` - omit fields whose value is `None` (great for `PATCH` responses)
- `exclude_unset=True` - omit fields that were never set by the caller, keeping only what was explicitly provided
- `by_alias=True` - use field aliases instead of field names (covered below)

That `exclude_unset` flag is the key to clean `PATCH` support. When a caller sends a partial update, you want to know which fields they actually included versus which ones they left out, so you don't accidentally overwrite unspecified fields with `None`. Pydantic tracks that for you.

---

### `Aliases` — Handling External Naming Conventions

JavaScript APIs use `camelCase`. Python uses `snake_case`. If you're consuming a third-party API (or producing one for a JS frontend), you hit this mismatch constantly.

Aliases let a field have a different name in the serialized form than in your Python code:

```python
from pydantic import BaseModel, Field, ConfigDict

class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")

# Accepts camelCase input:
u = User(firstName="Ada", lastName="Lovelace")
print(u.first_name)  # "Ada"

# Emits camelCase output when asked:
u.model_dump(by_alias=True)
# {'firstName': 'Ada', 'lastName': 'Lovelace'}
```

The `populate_by_name=True` config flag means you can pass data in using *either* the alias or the Python name, which is forgiving. If you'd rather enforce one or the other, leave it off.

For whole-class rules (like "always convert snake_case to camelCase"), there's `alias_generator`, which takes a function that transforms every field name automatically — you don't have to write `Field(alias=...)` on every line.

---

### `computed_field` — Derived Values in Output

Sometimes you want a field that isn't *stored* on the model but is *computed* from other fields, and you want it to appear in the serialized output. That's `@computed_field`:

```python
from pydantic import BaseModel, computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

r = Rectangle(width=3, height=4)
r.model_dump()
# {'width': 3.0, 'height': 4.0, 'area': 12.0}
```

Without `@computed_field`, `area` would be a regular property you could access in Python but it wouldn't appear in `.model_dump()`. Adding the decorator tells Pydantic "include this in serialization and in the JSON Schema." Great for returning response fields like `full_name` from `first_name + last_name`, or `total_price` from `unit_price * quantity`.

---

### `Schema Generation` — The Quiet Superpower

Every Pydantic model can emit a **JSON Schema** describing itself:

```python
Card.model_json_schema()
# {
#     "title": "Card",
#     "type": "object",
#     "properties": {
#         "name": {"type": "string", "title": "Name"},
#         "cost": {"type": "integer", "title": "Cost"},
#         ...
#     },
#     "required": ["name", "cost"]
# }
```

This is the single feature that makes FastAPI's `/docs` page work. FastAPI walks through your app's route handlers, asks every Pydantic model in every request and response for its JSON Schema, and assembles the whole thing into an OpenAPI document. Swagger UI reads that document and renders the interactive docs page you see at `/docs`. You wrote zero lines of documentation code — it all came from type hints and `Field` constraints.

This is also why keeping your Pydantic models clean matters. A well-structured model with good field names, sensible defaults, and clear constraints produces good docs. A sloppy model with `Any` types and no constraints produces sloppy docs.

---

### `TypeAdapter` — Pydantic Without a Model

Sometimes you want Pydantic's validation on a type that isn't a full `BaseModel`. Maybe you just have a `list[int]`, or a `dict[str, User]`, or a tagged union. You don't want to wrap it in a `BaseModel` just to validate it.

`TypeAdapter` is the escape hatch:

```python
from pydantic import TypeAdapter

IntList = TypeAdapter(list[int])

IntList.validate_python([1, 2, 3])       # [1, 2, 3]
IntList.validate_python(["1", "2", "3"]) # [1, 2, 3]  (coerced)
IntList.validate_json("[1, 2, 3]")       # [1, 2, 3]
```

Anywhere you'd use `BaseModel` methods, `TypeAdapter` gives you the equivalent: `validate_python`, `validate_json`, `dump_python`, `dump_json`, `json_schema`. The difference is `TypeAdapter` works on any type annotation, not just a subclass of `BaseModel`.

You'll hit this when you need to validate a list of items without creating a wrapper model, or when you want to validate data matching a complex `Union` type.

---

### `model_config` — Per-Model Settings

You've already seen `model_config` a few times above. It's the central place to turn on flags that change how a model behaves:

```python
from pydantic import BaseModel, ConfigDict

class Card(BaseModel):
    model_config = ConfigDict(
        strict=True,              # reject type coercion
        frozen=True,              # make instances immutable
        extra="forbid",           # reject unknown fields
        str_strip_whitespace=True,# auto-strip whitespace from string fields
        populate_by_name=True,    # allow both alias and field name on input
    )
    ...
```

A few of these deserve a closer look:

#### Highlights:
- `extra="forbid"` - by default, extra fields in the input are silently ignored. Setting this to `"forbid"` turns unknown fields into validation errors. Good for catching typos in request bodies.
- `frozen=True` - makes the model immutable after construction. Assigning to a field raises an error. Useful for value-object-style modeling.
- `str_strip_whitespace=True` - applies `.strip()` to every string field automatically. A one-liner that saves a lot of custom validators.

There are dozens more flags. When something feels like it should be a global toggle, check `ConfigDict` first before writing custom validators.

---

### `Nested Models` — Composition Just Works

Models can contain other models, and Pydantic validates all the way down:

```python
class Address(BaseModel):
    street: str
    city: str
    postal_code: str

class User(BaseModel):
    name: str
    address: Address

u = User(name="Ada", address={"street": "123 Main", "city": "London", "postal_code": "SW1"})
print(u.address.city)  # "London"
```

When you pass a dict for `address`, Pydantic notices the annotated type is `Address` and recursively constructs that model from the dict. If the nested data is invalid, the error message tells you the exact path: `address.postal_code`. This works to arbitrary depth, including `list[SomeModel]`, `dict[str, SomeModel]`, optional nested models, and tagged unions.

This is the feature that makes Pydantic scale from "one endpoint with three fields" to "a production API with dozens of nested schemas." Composition is basically free.

---

### `pydantic-settings` — The Same Engine, Applied to Config

You already saw this in Lesson 11, but it's worth naming explicitly here: `pydantic-settings` is not a separate library with its own rules. It's a thin layer that points Pydantic's parsing-and-validation engine at environment variables and `.env` files instead of at request bodies. Every feature in this doc — field constraints, validators, aliases, nested models, `SecretStr` — works inside a `BaseSettings` class the exact same way.

That's the reuse story: once you've learned Pydantic, you get configuration management for free. And you get CLI arg parsing (via `pydantic-argparse`), database integration (via SQLModel), and form parsing (via FastAPI's `Form` handling) using the same mental model.

---

### `v1 vs v2` — A Quick Historical Note

Pydantic had a major version bump from v1 to v2 in 2023, and the internals were rewritten in Rust (`pydantic-core`) for a big speed boost. A lot of the method names changed in the process, so if you find an old Stack Overflow answer or blog post, the code may not match what you've been learning.

#### Renames to know:
- `.dict()` → `.model_dump()`
- `.json()` → `.model_dump_json()`
- `.parse_obj()` → `.model_validate()`
- `.parse_raw()` → `.model_validate_json()`
- `.schema()` → `.model_json_schema()`
- `@validator` → `@field_validator`
- `@root_validator` → `@model_validator`
- `class Config:` → `model_config = ConfigDict(...)`

Everything you're writing in this learning project is v2 syntax, which is correct. Just be aware that older tutorials may show the old names, and don't let that confuse you — it's the same library, just renamed.

---

## When NOT to Use Pydantic

This is easy to miss because Pydantic is so pleasant to work with — once you're comfortable with it, you start wanting to use `BaseModel` for everything. But Pydantic's sweet spot is **the edges of your app**: the places where data crosses a trust boundary. An HTTP request arrives, you validate it with Pydantic. A database row comes back, you serialize it with Pydantic. An environment variable needs parsing, you use `BaseSettings`.

Between those edges — the internal logic of your application — plain dataclasses or regular classes with type hints are often the better tool. A Pydantic maintainer (Pozz_ on Reddit) put it well. Consider *not* using Pydantic when:

- **You have to set `arbitrary_types_allowed=True` in the config.** This is a sign that your model is holding objects Pydantic doesn't know how to validate (database connections, HTTP clients, custom service objects). At that point you're fighting the library instead of using it.

- **Your model represents more than data.** If it has internal state, manages a connection pool, coordinates with other services, or has methods that do things beyond getting/setting fields — it's not a data model, it's a service. Use a regular class.

- **Your model is only instantiated directly in code, never from external input.** If you're constructing an object yourself and you control every argument, a static type checker (like mypy or pyright) already catches type errors at development time. Pydantic's runtime validation is overhead you don't need here.

The rule of thumb: **Pydantic at the boundary, dataclasses in the middle.** Use Pydantic to validate what comes in (requests, config, external API responses) and serialize what goes out (API responses, JSON exports). For intermediate data structures that live entirely inside your app's logic, `@dataclass` gives you the same structured feel with less machinery.

```python
from dataclasses import dataclass

@dataclass
class DamageCalculation:
    base_damage: int
    multiplier: float
    is_critical: bool

    @property
    def total(self) -> int:
        damage = self.base_damage * self.multiplier
        return int(damage * 2 if self.is_critical else damage)
```

No parsing, no serialization, no schema generation — because this object never leaves your process. It's constructed in code, used in code, and discarded. A dataclass is the right weight for that job.

---

## The Mental Model to Walk Away With

Stop thinking of Pydantic as "validation." Start thinking of it as **one class that owns the shape of your data**. From that one class you get:

- A type-safe constructor that parses raw input into a clean object.
- Validation with precise error messages for free.
- A serializer that converts the object back into any external format.
- Auto-generated documentation that stays in sync with your code.
- The same behavior everywhere it's used — API bodies, config files, CLI args, database rows.

When you write `class Card(BaseModel)`, you're not declaring a validator. You're declaring a *contract*: this is what a Card looks like, everywhere in my system, forever. Every feature in this doc is just a different way of reading, writing, or enforcing that contract.

That's why FastAPI built its whole API design philosophy on top of it — and why, once you internalize it, you'll keep reaching for Pydantic even in places that have nothing to do with web frameworks.
