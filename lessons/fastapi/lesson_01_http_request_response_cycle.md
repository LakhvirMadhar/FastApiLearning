# Lesson 01: HTTP Request/Response Cycle

## What We're Doing
Understanding how computers talk to each other over the web — the foundation that everything in FastAPI sits on top of.

## Why / Context

Before you write a single line of FastAPI code, you need to understand HTTP. Here's why: FastAPI is a framework for building **HTTP APIs**. Every single thing it does — routing, validation, responses — is just a nice Python wrapper around HTTP concepts. If you don't understand HTTP, you'll be memorizing syntax without knowing what it actually does. Once HTTP clicks, FastAPI will feel intuitive instead of magical.

Think of it this way: HTTP is like the postal system. There are rules about how to address an envelope, what goes inside, and what the recipient sends back. FastAPI is just a really efficient post office that handles all of that for you — but you still need to understand how mail works.

## Concepts

### Concept: `HTTP` — What It Actually Is

HTTP stands for **HyperText Transfer Protocol**. That's a fancy name for a simple idea: it's a set of rules for how two computers communicate over the internet. One computer (the **client** — usually a browser or an app) sends a **request**, and the other computer (the **server**) sends back a **response**. That's it. Every single interaction on the web follows this pattern.

It's always the client that initiates. The server just sits there waiting. A client says "hey, give me this page" or "hey, save this data" and the server responds. The server never randomly reaches out to the client on its own (at least not with plain HTTP — websockets are a different story, but ignore that for now).

This is called a **request/response cycle**, and it's the heartbeat of the web.

---

### Concept: `HTTP Request` — What the Client Sends

When a client talks to a server, it sends a structured message called a request. Every HTTP request has a few key parts:

#### Parts of a Request:

- **Method** — What you want to do (GET, POST, PUT, DELETE — more on these below)
- **URL** — Where you want to do it (like `/users` or `/items/42`)
- **Headers** — Metadata about the request (like "I'm sending JSON" or "here's my login token")
- **Body** — The actual data you're sending (not every request has one — more on this below)

Here's what a raw HTTP request looks like conceptually:

```
POST /users HTTP/1.1
Host: api.example.com
Content-Type: application/json
Authorization: Bearer some-token-here

{
    "name": "Alex",
    "email": "alex@example.com"
}
```

Let's break this down line by line:

- `POST /users HTTP/1.1` — Three things crammed into one line: the **method** (`POST` — you're creating something), the **path** (`/users` — where on the server you're sending it), and the **protocol version** (`HTTP/1.1` — just says "I'm speaking HTTP version 1.1," you'll never change this).
- `Host: api.example.com` — A header that says which server you're talking to. This is how one server can host multiple different websites/APIs — the Host header tells it which one you mean.
- `Content-Type: application/json` — A header telling the server "the body I'm sending you is in JSON format." Without this, the server wouldn't know how to interpret the data blob you're sending. `Content-Type` is a header, not its own special thing — it's just one of the key-value pairs alongside `Host` and `Authorization`. In API work it's almost always `application/json`, but other values exist like `text/html` for web pages or `multipart/form-data` for file uploads.
- `Authorization: Bearer some-token-here` — A header that proves who you are. The `Bearer` part is just a convention that means "here's a token." The token itself is a long string the server gave you when you logged in. Think of it like a wristband at a concert — you show it to prove you're allowed in.
- The JSON block at the end is the **body** — the actual data you're creating (the new user's info).

---

### Concept: `HTTP Methods` — The Verbs of the Web

The method tells the server **what kind of action** you want to perform. There are several HTTP methods, but these four are the ones you'll use constantly:

#### The Big Four:

- **GET** — "Give me something." You're asking the server to send you data. When you type a URL into your browser and hit enter, that's a GET request. When you load a list of users, that's GET. **GET requests don't have a body** — you're just asking for data, you're not sending any. Think of it like asking a librarian to show you a book. You don't hand them anything, you just ask.

- **POST** — "Here's something new, save it." You're sending data to the server to create a new resource. Submitting a sign-up form? That's POST. Creating a new blog post? POST. **POST requests have a body** — that's where the new data lives. Think of it like handing the librarian a new book and saying "add this to the collection."

- **PUT** — "Replace this thing with what I'm giving you." You're sending data to update an existing resource. If a user changes their email address, you'd PUT the updated user data. **PUT requests have a body** — the updated data. Think of it like handing the librarian a revised edition and saying "swap out the old copy."

- **DELETE** — "Get rid of this." You're asking the server to remove something. Deleting your account? That's DELETE. **DELETE requests usually don't have a body** — you're just pointing at something and saying "remove it." Like telling the librarian "pull that book off the shelf."

There are others (PATCH, OPTIONS, HEAD), but these four cover the vast majority of what you'll build.

Notice the pattern: GET and DELETE are about pointing at things ("give me that" / "remove that"), so they typically don't need a body. POST and PUT are about sending data ("here's something new" / "here's an update"), so they do need a body.

---

### Concept: `HTTP Response` — What the Server Sends Back

After the server processes your request, it sends back a response. Every HTTP response has:

#### Parts of a Response:

- **Status code** — A number that tells you what happened (did it work? did something go wrong?)
- **Headers** — Metadata about the response (what format is the data in, how big it is, etc.)
- **Body** — The actual data being sent back (a JSON object, an HTML page, an error message, etc.)

Here's what a response looks like conceptually:

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "id": 1,
    "name": "Alex",
    "email": "alex@example.com"
}
```

Line by line:

- `HTTP/1.1 200 OK` — The server saying "I speak HTTP 1.1, and your request was successful" (`200 OK`).
- `Content-Type: application/json` — Same idea as the request header — the server telling you "what I'm sending back is JSON."
- The JSON block is the **body** — the server sends back the user it just created. Notice it now has `"id": 1` that wasn't in the request. The server assigned that. This is a common pattern: you send the data, the server adds its own fields (like an ID or a timestamp) and sends the complete object back.

---

### Concept: `Status Codes` — The Server's Short Answer

Status codes are three-digit numbers that tell you the result of your request at a glance. They're grouped by their first digit:

#### The Groups:

- **2xx — Success.** Your request worked.
- **4xx — Client error.** You (the client) messed something up.
- **5xx — Server error.** The server messed something up.

You don't need to memorize all of them. Here are the ones you'll actually see all the time:

#### The Ones That Matter:

- **200 OK** — The most common one. "Here's what you asked for." Used for successful GET requests, and sometimes for successful PUT/DELETE.

- **201 Created** — "I made the thing you asked me to make." Used after a successful POST. The difference from 200 is subtle but meaningful — 201 specifically means a new resource was created.

- **204 No Content** — "Done, but I have nothing to send back." Often used for DELETE — the thing is gone, there's nothing to return. The response body is empty.

- **400 Bad Request** — "I don't understand what you sent me." The client sent something malformed or nonsensical. Like sending text where a number was expected.

- **404 Not Found** — You already know this one. "That thing doesn't exist." You tried to GET, PUT, or DELETE something, but the URL doesn't point to anything real.

- **422 Unprocessable Entity** — "I understand what you sent, but it doesn't pass validation." This is a big one in FastAPI — when someone sends data that doesn't match your Pydantic model, FastAPI automatically returns a 422 with a detailed error message explaining what went wrong. You'll see this a lot.

- **500 Internal Server Error** — "Something broke on my end." The server crashed, hit a bug, or something unexpected happened. When you see this, the problem is in the server code, not the client's request.

Here's a quick way to remember the groups: **2xx = happy, 4xx = client's fault, 5xx = server's fault**.

---

### Concept: `Headers` — Metadata About the Message

Headers are key-value pairs that ride along with both requests and responses. They don't contain the main data — they contain information *about* the data. Think of them like the label on a shipping box: the label tells you what's inside, where it's going, and how to handle it, but it's not the actual contents.

#### Common Headers You'll See:

- **Content-Type** — Tells the other side what format the body is in. For APIs, this is almost always `application/json`. When FastAPI sends back a response, it automatically sets this header to `application/json` for you.

- **Authorization** — How the client proves who they are. Usually looks like `Bearer some-long-token-here`. When you get to the authentication lesson, you'll be working with this header a lot.

- **Accept** — The client telling the server "I'd prefer the response in this format." Usually `application/json` for APIs.

You don't need to memorize every header that exists. Just know that they're there, and that Content-Type and Authorization are the ones you'll interact with most when building APIs.

---

### Concept: `Request/Response Bodies` — The Actual Data

The body is where the real content lives. In API work, bodies are almost always **JSON** (we'll cover JSON properly in Lesson 02, but you've probably seen it before — curly braces, key-value pairs).

#### When Bodies Exist:

- **Requests:** POST and PUT have bodies (you're sending data). GET and DELETE usually don't (you're just pointing at something).
- **Responses:** Most responses have bodies (the server is sending data back). The exception is 204 No Content — the server explicitly says "I have nothing to send back."

When FastAPI receives a request with a body, it automatically parses the JSON and validates it against your Pydantic model. When it sends a response, it automatically converts your Python objects into JSON. You'll see this in action once we start writing code — it's one of the best parts of the framework.

---

## Your Task

No code for this lesson — this is all conceptual groundwork. But to make sure it stuck, think through these scenarios:

1. A user opens your app and sees a list of their bookmarks. What HTTP method was used to fetch that list? What status code would the server return?

2. A user fills out a form to create a new bookmark. What method sends that data to the server? What status code should the server return if it worked?

3. A user clicks "delete" on one of their bookmarks. What method is that? What status code makes sense for the response?

4. A user tries to visit `/bookmarks/999` but bookmark 999 doesn't exist. What status code does the server return?

5. A user submits a form but leaves the URL field empty, and your API requires it. What status code should the server return?

When you've thought through those, let me know and we'll move on to Lesson 02 where we'll cover APIs and JSON.
