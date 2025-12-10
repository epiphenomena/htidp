This is a wise choice. **Go (Golang)** is significantly better for a reference implementation than Zig. It is readable, widely understood, garbage-collected (safer for reference logic), and has a production-grade standard library for HTTP and JSON.

Here is the revised **System Preamble** and the **Granular Prompt Strategy**. I have broken the "Build the Server" and "Build the Client" tasks into much smaller, atomic units that an agent can complete successfully in a single pass.

### **Part 1: The AI Agent Preamble**

*Replace the previous preamble with this version.*

***

**[START PREAMBLE]**

**PROJECT CONTEXT: HTIDP (HyperText Identity Protocol)**
You are the Lead Architect and Developer for **HTIDP**, a decentralized, web-native identity protocol.

**CORE PHILOSOPHY:**
1.  **Identity is a URL:** Users connect to servers (`https://alice.com`), not devices.
2.  **HATEOAS Discovery:** Beyond `/.well-known/htidp`, never hardcode paths. Clients must follow JSON links.
3.  **Polyglot Extensibility:** Data keys are URLs (Namespaces). Clients ignore keys they don't understand.
4.  **Privacy by Default:** Connections are unique. Data is pulled (polled), not pushed.
5.  **Delegated Trust:** Organizations can sign credentials for employees, and employees can inherit connection authorization from the organization.

**TECH STACK:**
* **Specification:** OpenAPI / JSON Schema.
* **Reference Server:** **Go (Golang)**. Standard library `net/http` preferred over heavy frameworks.
* **Reference Client:** Vanilla HTML/JS (PWA).
* **Crypto:** Ed25519 for signing/verification.

**YOUR GOAL:**
Build the specification, the Go reference server, and the PWA client step-by-step. Focus on modularity and strict adherence to the protocol's discovery rules.

**[END PREAMBLE]**

***

### **Part 2: The Detailed Prompt Breakdown**

I have exploded the previous 6 prompts into **12 granular steps**. This ensures the agent doesn't hallucinate complexity or skip error handling.

#### **Phase 1: The Specification (The Truth Source)**

**Prompt 1: Core Data Structures**
> **Task:** Define the JSON Data Models for HTIDP (No server code yet).
> **Requirements:**
> 1.  Define the **Identity Object** (The Profile). Use the namespace `https://htidp.org/ns/vcard` for fields: `fn` (Full Name), `photo`, `note`.
> 2.  Define the **Handshake Request**. Fields: `requester_id` (URL), `timestamp`, `intro_text` (max 280 chars), `public_key` (Base64), `signature`.
> 3.  Define the **Handshake Response**. Fields: `status` (pending/accepted), `token` (if accepted), `links` (array of rel/href).
> 4.  Output a JSON file `schema_examples.json` containing valid example objects for both.

**Prompt 2: The Discovery & HATEOAS Flow**
> **Task:** Define the API Navigation Flow.
> **Requirements:**
> 1.  Create a text document describing the flow:
>     * Step 1: `GET /.well-known/htidp` -> Returns `{ "api_root": "..." }`.
>     * Step 2: `GET [api_root]` -> Returns links to `handshake` (POST) and `identity` (GET).
> 2.  Define the **Delegation Extension** logic: How an Organization includes a `delegate` link in their root API to allow employees to request inherited access.

---

#### **Phase 2: The Go Reference Server (Foundation)**

**Prompt 3: Go Project Skeleton & Discovery**
> **Task:** Initialize the Go Server.
> **Requirements:**
> 1.  `go mod init htidp-server`.
> 2.  Create `main.go`. Use standard `net/http`.
> 3.  Create a struct `Config` to hold the hostname (e.g., `localhost:8080`).
> 4.  Implement `GET /.well-known/htidp`. It must return JSON pointing to `/api/v1` (or whatever internal path you choose).
> 5.  Implement `GET /api/v1`. It must return a HATEOAS response with a `rel: "https://htidp.org/rel/handshake"` link.
> **Constraint:** Do not implement the handshake logic yet. Just the routing and JSON marshaling.

**Prompt 4: Handshake Storage & State (In-Memory)**
> **Task:** Implement the Storage Layer for Connections.
> **Requirements:**
> 1.  Create `store.go`.
> 2.  Define a `Connection` struct: `ID`, `RequesterURL`, `IntroText`, `PublicKey`, `Status` (Pending/Active), `AccessToken`.
> 3.  Implement a thread-safe (Mutex) map to store these connections.
> 4.  Implement a helper function `GenerateToken()` that returns a secure random string.

**Prompt 5: Implementing the Handshake Endpoint**
> **Task:** Implement `POST [handshake_url]`.
> **Requirements:**
> 1.  Accept the JSON payload defined in Prompt 1.
> 2.  Validate `intro_text` length (<280 chars).
> 3.  **Crucial:** Ignore the signature verification for this step (mark with `TODO`).
> 4.  Save the request to the store with status `Pending`.
> 5.  Return HTTP 202 Accepted with a JSON body containing a "check_status" link.

**Prompt 6: The Admin Approval Flow (Mock UI)**
> **Task:** Create a simple Admin interface to approve requests.
> **Requirements:**
> 1.  Create an endpoint `GET /admin/requests` that lists Pending connections (and shows the `intro_text`).
> 2.  Create an endpoint `POST /admin/approve/{id}`.
>     * Updates status to `Active`.
>     * Generates an `AccessToken`.
> 3.  Update the `POST [handshake_url]` logic: If the requester polls the status link and is now `Active`, return the `AccessToken`.

---

#### **Phase 3: The Security Layer (Crypto)**

**Prompt 7: Ed25519 Signature Verification**
> **Task:** Secure the Handshake.
> **Requirements:**
> 1.  Update `store.go` to store the Server's own Private/Public Key pair (generate on startup if missing).
> 2.  Create a `crypto_utils.go` file. Implement `VerifySignature(pubKey, message, signature)`.
> 3.  Update the Handshake Handler (from Prompt 5):
>     * Reconstruct the "signed string" from the payload fields (canonicalize the JSON or concatenate fields).
>     * Verify the signature. Return 400 if invalid.

**Prompt 8: Authorized Data Access**
> **Task:** specific endpoint to serve Contact Data.
> **Requirements:**
> 1.  Create a Middleware `RequireToken`.
>     * Check the `Authorization: Bearer <token>` header.
>     * Look up the token in the Store. If missing, 401.
> 2.  Implement `GET /api/me` (or the discovered profile URL).
>     * Apply `RequireToken`.
>     * Return the server owner's vCard JSON.

---

#### **Phase 4: The Client (PWA)**

**Prompt 9: Client Discovery Engine**
> **Task:** Build the JavaScript Discovery Logic.
> **Requirements:**
> 1.  Create `client.js`.
> 2.  Implement a function `async discover(domain)`:
>     * Fetch `https://domain/.well-known/htidp`.
>     * Parse `api_root`.
>     * Fetch `api_root`.
>     * Find and return the `handshake` URL.
> 3.  Handle CORS errors gracefully (assume server allows `*` for now).

**Prompt 10: Client Handshake UI**
> **Task:** Build the Connection UI.
> **Requirements:**
> 1.  Create `index.html` with a form: "Target Domain" and "Intro Text".
> 2.  On Submit:
>     * Generate a client-side KeyPair (Ed25519).
>     * Run `discover()`.
>     * Construct the payload, sign it, and POST to the handshake URL.
>     * Display "Request Sent. Waiting for approval..."

---

#### **Phase 5: The Organization & Delegation Extensions**

**Prompt 11: Organization Directory Structure**
> **Task:** Implement Organization Mode for the Go Server.
> **Requirements:**
> 1.  Add a flag to `Config`: `IsOrganization bool`.
> 2.  If `IsOrganization` is true:
>     * The Root API response must include a new link: `rel: "https://htidp.org/rel/directory"`.
>     * Implement the Directory Endpoint: Returns a list of Departments (Name + Identity URL).



**Prompt 12: The Delegation Logic (Inheritance)**
> **Task:** Implement the "Delegated Access" flow.
> **Requirements:**
> 1.  **New Endpoint:** `POST /api/delegate` (Internal/Admin only).
>     * Input: `parent_token` (The token Bob gave to Acme), `employee_id`.
>     * Logic: Validate `parent_token`. Generate a new `child_token`.
>     * Store `child_token` with metadata: `linked_to: parent_token`.
> 2.  **Update Middleware:**
>     * Update `RequireToken` to handle linked tokens. If a child token is used, log the access as "Delegated by [Parent]".

### **Part 3: Visual Aids**

When you reach the documentation phase, use these descriptions to generate diagrams (or ask the agent to generate Mermaid.js code):

1.  **The "HATEOAS Ladder":** A diagram showing how the client climbs from `.well-known` -> `API Root` -> `Handshake URL` -> `Poll Status` -> `Access Token`.
2.  **The Delegation Chain:** A sequence diagram showing:
    * Bob -> Grants Token A to Acme.
    * Acme -> Grants Token B (linked to A) to Alice.
    * Alice -> Uses Token B to fetch Bob's info.
    * Bob's Server -> Checks Token B -> Sees linkage to Token A -> Allows.