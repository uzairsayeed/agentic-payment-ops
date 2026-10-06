# MCP Learning Checkpoint — Lessons 1 to 6A

> **Purpose:** Quick revision of everything covered so far before we start the real portfolio system.  
> **Scope:** MCP fundamentals, tools, discovery, transports, Inspector, clients, protocol evolution, and the experiments we ran.

---

## 1. Why MCP exists

An LLM does **not** automatically know how to access our APIs, databases, files, logs, or business services.

Without MCP, every AI application can end up needing custom integration code.

```text
AI App
  ↓
custom integration
  ↓
Payment API
```

MCP gives AI applications a **standard way to discover and use external capabilities**.

```text
AI App
  ↓
MCP
  ↓
MCP Server
  ↓
Business System
```

### Core definition

**MCP = Model Context Protocol**

It is a **protocol**, not an application.

Useful analogy:

```text
HTTP = protocol
FastAPI / Express = applications using HTTP

MCP = protocol
MCP client / MCP server = applications/components using MCP
```

---

## 2. Core MCP roles

### Host

The application containing the AI experience.

Examples:
- Cursor
- Claude Code
- VS Code
- our future custom AI operations application

### MCP Client

The component inside the host that speaks MCP to an MCP server.

Its responsibilities include:
- connect to a server;
- discover capabilities;
- invoke tools;
- receive results.

### MCP Server

A program that exposes capabilities using MCP.

Example:

```text
Payment MCP Server

get_payment
get_payment_timeline
retry_payment
```

### Tool

A capability that can be invoked.

Example:

```text
get_payment(payment_id)
```

The tool can internally call:
- REST APIs;
- databases;
- application code;
- another service.

MCP does **not** dictate the internal implementation.

---

## 3. Important architecture distinction

A normal backend might already expose:

```text
GET /payments/PAY-123
```

The MCP server can expose an AI-friendly capability:

```text
get_payment("PAY-123")
        ↓
GET /payments/PAY-123
```

So:

```text
MCP Server != Payment Backend
```

The MCP server can sit **in front of** an existing backend.

```text
AI Host
   ↓
MCP Client
   ↓ MCP
Payment MCP Server
   ↓ REST
Payment Service
   ↓
Database
```

MCP does **not replace REST**.

---

## 4. How the host knows which tools exist

The host does not need every tool hard-coded.

Its MCP client can ask the server:

```text
tools/list
```

SDK-level example:

```python
tools = await client.list_tools()
```

The server returns definitions such as:

```text
name:
get_payment

description:
Retrieve payment details using a payment ID.

input:
payment_id: string
```

This is **tool discovery**.

Then later:

```text
tools/call
```

executes a selected tool.

### Remember

```text
tools/list = DISCOVERY
tools/call = EXECUTION
```

---

## 5. Anatomy of an MCP tool

A tool has two important sides:

```text
Tool
├── Contract / definition
└── Implementation
```

### Contract

Includes:
- name;
- description;
- input schema;
- optionally output schema.

Example:

```json
{
  "name": "get_payment",
  "description": "Retrieve payment details using a payment ID",
  "inputSchema": {
    "type": "object",
    "properties": {
      "payment_id": {
        "type": "string"
      }
    },
    "required": ["payment_id"]
  }
}
```

### Implementation

Normal application code:

```python
def get_payment(payment_id: str):
    ...
```

### Why descriptions matter

Later, an LLM may decide which tool to call partly from:
- tool name;
- description;
- schema.

Bad descriptions can cause bad tool selection.

### Why schemas matter

A probabilistic model may generate incorrect arguments.

The schema gives us a deterministic contract.

---

## 6. Our first MCP server

We created a learning-only server:

```python
from mcp.server import MCPServer

mcp = MCPServer("payment-lab")

@mcp.tool()
def get_payment(payment_id: str) -> dict:
    """Retrieve payment details using a payment ID."""
    ...
```

The SDK derives useful MCP metadata from normal Python:

```text
function name
    ↓
tool name

docstring
    ↓
tool description

payment_id: str
    ↓
input JSON schema
```

The dictionary used inside this lab is **only learning scaffolding**.

It is not our portfolio backend.

---

## 7. Transport: how MCP messages travel

MCP defines the protocol.

A **transport** answers:

> How do the messages move between client and server?

We studied:

1. **stdio**
2. **Streamable HTTP**

---

## 8. stdio transport

`stdio` = standard input / standard output.

Typical local flow:

```text
client.py
   │
   │ launches
   ▼
server.py
```

The OS wires dedicated pipes:

```text
client write ─────────► server stdin
client read  ◄───────── server stdout
```

Important:

- no host/port;
- no network discovery;
- normally a specific parent-child process relationship;
- the client knows exactly which command to run.

Example:

```python
StdioServerParameters(
    command="uv",
    args=["run", "mcp", "run", "server.py"]
)
```

This is how `client.py` knows about `server.py`.

It does **not** discover every stdio server running on the machine.

### Multiple stdio servers

Each connection has its own process and pipes.

```text
Client A ↔ Payment Server process
Client B ↔ Compliance Server process
Client C ↔ Observability Server process
```

There is no global "listen to all stdio clients" concept.

---

## 9. MCP Inspector

We ran:

```bash
uv run mcp dev server.py
```

This launched **MCP Inspector**.

Inspector acted as a development/test host with MCP client functionality.

When we toggled **Connect**, Inspector launched something like:

```bash
uv run --with mcp==2.3.0 mcp run server.py
```

Then:

```text
Inspector
   ↕ stdio
server.py
```

### Protocol panel

Inspector showed messages such as:

```text
TOOLS/LIST
PROMPTS/LIST
RESOURCES/LIST
TOOLS/CALL
```

This is a protocol trace.

It helped us see that MCP is not magic: concrete messages are exchanged.

### Edit & Replay

We:
1. called `get_payment`;
2. opened the recorded `tools/call`;
3. changed an argument;
4. replayed the MCP request.

This is useful for debugging.

Production systems will not rely on Inspector. Later we will use:
- OpenTelemetry;
- structured logs;
- metrics;
- audit/tool-call records;
- controlled scenario replay.

**OpenTelemetry is already locked into the final platform architecture.**

---

## 10. High-level MCP client

We used the convenient SDK abstraction:

```python
async with Client(server) as client:
    tools = await client.list_tools()
    result = await client.call_tool(...)
```

This hides lower-level details such as:
- transport setup;
- session/protocol setup;
- negotiation;
- cleanup.

This is convenient application code.

---

## 11. Low-level MCP client

We then exposed more mechanics:

```text
StdioServerParameters
        ↓
stdio_client
        ↓
read / write streams
        ↓
ClientSession
        ↓
initialize   (legacy path)
        ↓
list_tools
        ↓
call_tool
```

This taught us the difference between:

```text
transport
vs
MCP protocol session
vs
MCP operations
```

### Experiment: remove `initialize()`

When we removed:

```python
await session.initialize()
```

and called:

```python
await session.list_tools()
```

we received:

```text
MCPError: Invalid request parameters
```

This demonstrated the **legacy handshake-style lifecycle**.

---

## 12. MCP protocol evolution: old vs current

This matters because many tutorials online show older behavior.

### Handshake era — up to 2025-11-25

Typical lifecycle:

```text
initialize
    ↓
initialize response
    ↓
notifications/initialized
    ↓
tools/list
    ↓
tools/call
```

The client and server established a session before useful work.

This is why Inspector showed:

```text
LEGACY
NOTIFICATIONS/INITIALIZED
```

during our earlier experiment.

### Modern era — 2026-07-28

Key ideas:

- no mandatory `initialize` handshake;
- no protocol-level HTTP session requirement;
- `server/discover` is available for discovery/negotiation;
- requests can carry protocol/client metadata themselves;
- modern Streamable HTTP requests are designed to be self-contained.

The high-level Python SDK `Client(...)` defaults to **auto negotiation**:

```text
try server/discover
        ↓
modern server?
   YES → use modern protocol
   NO  → fall back to legacy initialize flow
```

We verified this ourselves.

Our HTTP client printed:

```text
Protocol version:
2026-07-28
```

So our current server/client successfully used the modern path.

---

## 13. SSE: old model vs Streamable HTTP

This is another area where old tutorials can be misleading.

### Older HTTP+SSE transport

The 2024-11-05 protocol used a separate **HTTP+SSE** transport model.

You may find tutorials explicitly talking about:

```text
HTTP endpoint
+
separate SSE stream
```

### Streamable HTTP

Streamable HTTP replaced the older HTTP+SSE transport starting in the 2025-03-26 protocol.

The 2026-07-28 revision simplified it further.

Modern mental model:

```text
single MCP HTTP endpoint
        ↓
client POSTs MCP request
        ↓
server responds with either:
- normal JSON response
or
- request-scoped SSE stream when streaming is needed
```

### Important takeaway

For new systems, we do **not** separately configure an "SSE transport".

We use:

```text
Streamable HTTP
```

and it can handle a request as:
- a normal JSON response;
- or an SSE stream when the request actually needs streaming.

So:

```text
Old:
HTTP + separate SSE transport model

Current:
Streamable HTTP
    └── JSON or request-scoped SSE as needed
```

Also, the 2026-07-28 revision removed the old GET streaming endpoint and protocol-level sessions for the modern path.

---

## 14. Our Streamable HTTP experiment

We ran the server independently:

```bash
uv run mcp run server.py --transport streamable-http
```

Then connected using:

```python
Client("http://localhost:8000/mcp")
```

Architecture:

```text
server.py
   │
   │ independently running
   ▼
localhost:8000/mcp
   ▲
   │ HTTP
client_http.py
```

This is different from stdio:

```text
stdio:
client launches server

HTTP:
server is already running;
client only knows its address
```

### What stayed the same

Even after changing transport:

```text
list_tools()
call_tool()
get_payment()
input schema
business behavior
```

all remained conceptually the same.

That proved:

> **Transport changes how messages travel, not what the MCP capability means.**

---

## 15. Why opening `/mcp` in Chrome failed

We opened the MCP endpoint directly in a browser and saw an error similar to:

```text
Bad Request: Missing session ID
```

Reason:

A browser navigation is just a normal HTTP GET.

It is **not a valid MCP client interaction**.

```text
Browser
  ↓ plain GET
MCP endpoint
  ↓
invalid MCP request
```

Whereas:

```text
MCP Client
  ↓ valid MCP protocol request + metadata
MCP endpoint
  ↓
success
```

An MCP HTTP endpoint is not a normal webpage or ordinary REST endpoint.

---

## 16. Error categories we observed

### A. Successful MCP call + successful business lookup

```text
payment_id = PAY-123
```

Result:
- tool contract valid;
- function executed;
- payment found.

### B. Successful MCP call + business NOT_FOUND

```text
payment_id = PAY-1234
```

Result:
- tool arguments valid;
- function executed;
- business result = `NOT_FOUND`.

Important:

```text
MCP success != business success
```

### C. Tool contract/schema failure

We deliberately sent:

```text
payment_idx
```

instead of:

```text
payment_id
```

The SDK rejected it before business code ran.

Result:

```text
is_error = true
```

Important:

```text
correct tool + invalid arguments
```

is a different failure from:

```text
wrong tool selected
```

This distinction will matter once an LLM generates tool arguments.

### D. Protocol/lifecycle failure

We skipped the legacy:

```python
session.initialize()
```

and attempted:

```python
session.list_tools()
```

Result:

```text
MCPError: Invalid request parameters
```

This failed at the MCP lifecycle layer.

So we already have several failure domains:

```text
protocol/lifecycle
tool contract/schema
business logic/result
transport/network
```

Later we will add:
- LLM tool-selection errors;
- orchestration errors;
- downstream provider errors;
- authorization/policy failures.

---

## 17. What the LLM does — and does NOT do

The LLM does **not** normally open the MCP network connection itself.

Later the flow will be:

```text
User
  ↓
Host
  ↓
LLM sees tool definitions
  ↓
LLM requests:
"call get_payment(payment_id=PAY-123)"
  ↓
Host/runtime
  ↓
MCP Client
  ↓
MCP Server
```

Better wording:

> **The LLM selects/requests a tool invocation. The host/runtime executes it through the MCP client.**

This distinction will matter when debugging.

---

## 18. Production observability direction

Inspector is for development.

Our portfolio system will use **OpenTelemetry end-to-end**.

Target trace:

```text
User request
  ↓
Agent Host / LangGraph
  ↓
LLM decision
  ↓
MCP Client
  ↓
MCP Server
  ↓
Payment Service
  ↓
Provider Simulator
  ↓
result back
```

We will capture:
- trace/workflow ID;
- MCP server;
- tool name;
- latency;
- status/error;
- downstream calls;
- policy/approval outcomes;
- retries/timeouts;
- safely redacted arguments.

This is a locked production requirement.

---

## 19. What we have NOT learned yet

We deliberately have **not** introduced:

- LLM integration;
- LangChain;
- LangGraph;
- multi-agent orchestration;
- resources;
- prompts;
- authentication/authorization;
- human approval;
- production persistence;
- real payment backend;
- evaluation harness.

That is intentional.

We first learned MCP itself.

---

## 20. Journey so far

```text
Lesson 1
Why MCP exists
+ Host / Client / Server / Tool

        ↓

Lesson 2
Tool definition
+ description
+ input schema
+ discovery vs invocation

        ↓

Lesson 3
Transport
+ stdio
+ Streamable HTTP mental model

        ↓

Lesson 4
First real MCP server
+ Inspector
+ tools/list
+ tools/call
+ schema validation

        ↓

Lesson 5
Low-level client
+ stdio pipes
+ ClientSession
+ legacy initialize lifecycle

        ↓

Lesson 6A
Streamable HTTP
+ independent server process
+ modern 2026-07-28 negotiation
+ protocol version verified
+ old SSE vs current Streamable HTTP
```

---

## 21. Fast interview recap

### What is MCP?

A protocol that standardizes how AI applications discover and invoke external capabilities such as tools, resources, and prompts.

### Is MCP an application?

No.

### Does an MCP server need an LLM?

No.

### Does MCP replace REST?

No. MCP can expose capabilities backed by REST APIs.

### How does a host know which tools exist?

Its MCP client performs tool discovery, e.g. `tools/list`.

### What is the difference between `tools/list` and `tools/call`?

```text
tools/list = discover
tools/call = execute
```

### What is stdio?

A local process transport using dedicated stdin/stdout pipes.

### Does a stdio server listen to every client on the machine?

No. A client usually launches/connects to a specific server process.

### Why use Streamable HTTP?

For independently deployed/shared MCP servers reachable over HTTP.

### Do we need a separate SSE transport today?

For new systems, no. Streamable HTTP replaced the older HTTP+SSE transport model and can return a request-scoped SSE stream when streaming is required.

### What changed in MCP 2026-07-28?

Modern MCP removed the mandatory initialize handshake and protocol-level HTTP sessions; `server/discover` and per-request metadata support a more stateless model.

---

## 22. Next checkpoint

We now stop extending the toy in-memory payment dictionary.

The next stage is:

```text
Learning Lab
      ↓
Portfolio System
```

We will build a real synthetic payment-operations platform with:
- persistent payment state;
- payment lifecycle;
- PostgreSQL;
- provider simulators;
- realistic failure scenarios;
- later MCP servers over real services;
- OpenTelemetry;
- LLM + LangChain + LangGraph;
- orchestration and evaluation.

The small labs remain for learning.

The portfolio system will be the substantial Senior/Staff-level engineering artifact.

---

## Official references

- MCP Python SDK v2: https://github.com/modelcontextprotocol/python-sdk
- Protocol versions: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/protocol-versions.md
- Python SDK v2 changes: https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/whats-new.md
- Streamable HTTP spec: https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/streamable-http.mdx
