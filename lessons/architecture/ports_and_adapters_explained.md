# Ports and Adapters (Hexagonal Architecture)

## What Is It

The industry calls this **Ports and Adapters** or **Hexagonal Architecture**. Both names are confusing. A more descriptive name would be **Plug-in Architecture** — your function doesn't care what's plugged into it, you just swap the plug.

The core problem it solves: if you hardcode a specific database inside your function, your function now knows too much. Change the database and you're changing code everywhere. The fix is to inject the database from outside so your function never knows what it's talking to.

---

## The Three Parts

There are three parts, though most explanations only mention two:

- **Devices** - the two things that want to communicate (your function and your database)
- **Port** - the interface/contract that defines the shape of what's allowed in
- **Adapter** - the concrete class that wraps a device and makes it fit the port

### The HDMI/VGA analogy

Your Nvidia graphics card has an HDMI port. Your monitor only has a VGA port. They can't talk directly — incompatible.

You get a VGA-to-HDMI adapter. Now they can communicate. Neither device changed. The adapter bridged the gap.

In code:
- **Graphics card** - your function
- **Monitor** - your database (MongoDB, Postgres, etc.)
- **Port** - the interface that defines what methods are required
- **Adapter** - the class that wraps the database and makes it conform to the port

### The flow

```
MongoDB (device) → MongoUserRepository (adapter) → UserRepository (port) → my_func (device)
```

---

## The Code

### The problem

```python
def my_func():
    db = MongoClient()  # tightly coupled — my_func knows it's MongoDB specifically
```

If you swap MongoDB for Postgres, you're changing `my_func`. If you have 50 functions like this, you're changing all 50.

### The fix — inject the dependency

```python
def my_func(db):
    db.save_user(user)  # my_func no longer knows what db is
```

But this alone isn't enough — you also need a contract so every database you inject speaks the same language.

---

## ABC vs Protocol

Two ways to define that contract in Python.

### ABC (Abstract Base Class) — explicit inheritance

```python
from abc import ABC, abstractmethod

class VectorStore(ABC):
    @abstractmethod
    def read(self, query: str): ...

    @abstractmethod
    def write(self, data: str): ...


class PineconeAdapter(VectorStore):  # must explicitly inherit
    def read(self, query: str):
        print(f"Pinecone reading: {query}")

    def write(self, data: str):
        print(f"Pinecone writing: {data}")


class WeaviateAdapter(VectorStore):  # must explicitly inherit
    def read(self, query: str):
        print(f"Weaviate reading: {query}")

    def write(self, data: str):
        print(f"Weaviate writing: {data}")


def my_func(db: VectorStore):
    db.write("some data")
    db.read("some query")


pinecone = PineconeAdapter()
weaviate = WeaviateAdapter()

my_func(pinecone)
my_func(weaviate)
```

If you forget to implement an abstract method, Python throws an error the moment you try to instantiate the class. Enforced at **runtime**.

### Protocol — no inheritance needed

```python
from typing import Protocol

class VectorStore(Protocol):
    def read(self, query: str): ...
    def write(self, data: str): ...


class PineconeAdapter:  # no inheritance — just needs the right methods
    def read(self, query: str):
        print(f"Pinecone reading: {query}")

    def write(self, data: str):
        print(f"Pinecone writing: {data}")


class WeaviateAdapter:  # no inheritance
    def read(self, query: str):
        print(f"Weaviate reading: {query}")

    def write(self, data: str):
        print(f"Weaviate writing: {data}")


def my_func(db: VectorStore):
    db.write("some data")
    db.read("some query")
```

Python doesn't enforce Protocol at runtime. Your type checker (Pylance in VS Code, or mypy) checks it during **static analysis** — it reads your code without running it and flags mismatches as red squiggles before you ever run anything.

Protocol is more flexible when you don't own the third-party classes and can't make them inherit from your base class.

### When to use which

- **ABC** - you own all the adapters, want Python to enforce the contract at runtime
- **Protocol** - you don't own the third-party code, or you prefer the type checker to catch it early

---

## Dual Write — Composite Class

If you want to write to two databases simultaneously, you don't change `my_func` at all. You write a composite adapter:

```python
class DualWriteAdapter(VectorStore):
    def __init__(self, primary: VectorStore, secondary: VectorStore):
        self.primary = primary
        self.secondary = secondary

    def read(self, query: str):
        return self.primary.read(query)  # read from one

    def write(self, data: str):
        self.primary.write(data)
        self.secondary.write(data)  # write to both


pinecone = PineconeAdapter()
weaviate = WeaviateAdapter()

dual = DualWriteAdapter(primary=pinecone, secondary=weaviate)

my_func(dual)  # my_func has no idea this is happening
```

`my_func` just calls `db.write()` like normal. The fan-out is handled inside the composite class.

---

## Scaling to Many Adapters

Writing adapters by hand works for a handful of providers. At hundreds or thousands it breaks down. Three approaches:

**1. Community-contributed adapters** — you define the interface, the community writes the adapters. LangChain does this. You maintain the protocol, they maintain the adapters. Scales the ecosystem, not your team's workload. Problem: adapters rot when nobody maintains them.

**2. Config-driven adapter** — if providers are similar enough (most LLMs have a `chat` endpoint with messages), one class handles all of them via config:

```python
class GenericAdapter(VectorStore):
    def __init__(self, config: dict):
        self.config = config  # base url, auth, field mappings etc

    def write(self, data: str):
        # generic HTTP call using config
        ...
```

One class, infinite providers via config. This is basically what LiteLLM does.

**3. Plugin spec** — expose an interface spec and let third parties write their own adapters that conform to it. Zapier, Slack, and Shopify do this. You define the spec, they build to it.

Most mature platforms end up doing all three.

---

## When the Abstraction Breaks Down

Ports and adapters works well when devices are genuinely interchangeable. When they're fundamentally different in capability, a shared interface either becomes too broad to be useful or too specific to one device.

Example: HyperGraphRAG in Neo4j. Neo4j traverses relationships across a knowledge graph — multi-hop reasoning, relationship weights, graph traversal. Pinecone does cosine similarity nearest-neighbor search. These are fundamentally different retrieval paradigms.

LangChain tried to abstract all vector stores behind one interface:

```python
# LangChain's approach — abstracting the implementation
class VectorStore:
    def similarity_search(self, query: str, k: int): ...
    def add_embeddings(self, vectors: list): ...
    def delete_index(self, index_name: str): ...
```

Now Neo4j is forced to implement `similarity_search` even though it does graph traversal, not similarity search. The interface leaks implementation details from one type of database onto everyone else.

---

## Abstract the Output, Not the Implementation

The fix is to define the interface at the point where you stop caring.

You stop caring after retrieval hands you chunks to inject into a prompt. So that's where the interface lives:

```python
# Right level — abstracting the output
class RAGProvider(Protocol):
    def retrieve(self, query: str) -> list[str]: ...
```

```python
class Neo4jProvider(RAGProvider):
    def retrieve(self, query: str) -> list[str]:
        # 15 hops across knowledge graph
        # relationship traversal
        # multi-hop reasoning
        # ... however neo4j does its thing
        return ["chunk1", "chunk2", "chunk3"]  # all your tool sees

class PineconeProvider(RAGProvider):
    def retrieve(self, query: str) -> list[str]:
        # cosine similarity
        # nearest neighbor search
        # ... however pinecone does its thing
        return ["chunk1", "chunk2", "chunk3"]  # same output shape


def inject_into_prompt(query: str, rag: RAGProvider) -> str:
    chunks = rag.retrieve(query)
    context = "\n".join(chunks)
    return f"Context:\n{context}\n\nUser query: {query}"
```

`inject_into_prompt` only ever sees `list[str]`. Everything behind `retrieve` is a black box. Neo4j can do graph traversal internally, Pinecone can do nearest-neighbor internally — you don't care. The output contract is the same.

This is related to three principles that don't have one unified name:
- **Encapsulation** - hide internals, expose only what the caller needs
- **Black box abstraction** - you know what goes in and what comes out, you don't care what happens inside
- **Separation of concerns** - retrieval is fully owned by the provider, injection is fully owned by your tool

---

## LangChain, Chains, and DSLs

LangChain's core idea was chaining operations as objects:

```python
chain = prompt | llm | output_parser
result = chain.invoke({"query": "what is RAG?"})
```

The problem is this is equivalent to:

```python
result = output_parser(llm(prompt.format(query="what is RAG?")))
```

Three function calls. But LangChain wraps it in so many abstraction layers — `Runnable`, `invoke`, LCEL (LangChain Expression Language) — that you need an hour of docs just to understand why `invoke` exists.

LCEL is a **DSL** — Domain Specific Language. A mini language built for one specific purpose. SQL is a DSL for querying databases. Regex is a DSL for pattern matching. LangChain's `|` operator and `invoke` method is a DSL for chaining LLM operations.

The tradeoff with DSLs: if the domain is complex enough and stable enough, a DSL can be expressive and worth learning. SQL is worth it. But if the domain is simple or the DSL keeps changing — like LangChain's did — you're paying the learning cost with no payoff. You'd have been better off writing plain Python.

LangChain also split into `langchain-core`, `langchain`, and `langchain-community` to manage the mess of community adapters — which made it harder to know what package you even needed. Most teams doing serious RAG work end up writing their own thin wrappers around native clients instead.

---

## LiteLLM — When the Abstraction Is Worth It

LiteLLM is worth using because LLM providers (OpenAI, Anthropic, Mistral, etc.) are genuinely similar — they all have a `chat` endpoint that takes messages and returns a response. The abstraction isn't lying about the underlying similarity.

Vector databases are not like this. They have fundamentally different capabilities, indexing strategies, metadata filtering syntax, and consistency models. A shared abstraction flattens all of that into the lowest common denominator and you lose what makes each one useful.

The rule: use an abstraction when the things being abstracted are genuinely interchangeable at the level you care about. Don't use one when they aren't.
