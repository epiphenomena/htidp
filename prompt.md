This is a comprehensive blueprint for **htidp**. It prioritizes your requirement for HATEOAS (Hypermedia) discovery—where the client follows links rather than constructing URLs—and the "unique connection" privacy model.

### **Part 1: The AI Agent Preamble**

Copy and paste the text below into the "System Instructions" or at the very top of your chat session with your coding agent (Claude, ChatGPT, or local LLM). It establishes the context, constraints, and philosophy for every subsequent task.

***

**[START PREAMBLE]**

**PROJECT CONTEXT: htidp Protocol**
You are the Lead Architect and Developer for **htidp**, a decentralized, web-native identity and connection protocol.

**CORE PHILOSOPHY & CONSTRAINTS:**
1.  **Identity is a URL:** Users connect to *servers*, not devices. An identity is effectively a root URL (e.g., `https://alice.com/api`).
2.  **No Hardcoded Paths:** Beyond the initial Discovery entry point, **never** assume a URL structure (e.g., do not hardcode `/v1/profile`). All endpoints must be discovered dynamically via JSON links provided in API responses.
3.  **Polyglot Extensibility:** The protocol does not use versions (v1, v2). It uses **Namespaced Extensions**. The JSON keys themselves are URLs pointing to the definition of that data or capability. Clients ignore keys (URLs) they do not recognize.
4.  **Privacy by Default:**
    * There is no global "public profile" unless explicitly enabled.
    * Every relationship is a **Unique Connection**. Alice does not just "add Bob"; Alice’s server generates a unique context/token for Bob that reveals only what Alice chooses to share with him.
    * Data access is Pull-based (Polling) with HTTP Caching (ETags), not Push.
5.  **Tech Stack:**
    * **Transport:** HTTP/1.1 or HTTP/2 (REST principles).
    * **Format:** JSON.
    * **Reference Servers:** Python (FastAPI/Flask) and Zig (Zap/Http.zig).
    * **Reference Client:** Progressive Web App (PWA) using standard Web APIs.

**YOUR GOAL:**
Build a specification and implementation that eliminates the "awkward handshake" of exchanging contact info, replacing it with a secure, verifiable, and revocable digital connection.

**[END PREAMBLE]**

***

### **Part 2: Project Outline & Implementation Roadmap**

This outline breaks the project into logical dependencies.

#### **Phase 1: The Specification (The "Paper" Work)**
* **Goal:** Define the JSON schemas and the HATEOAS flow.
* **Key Design:**
    * **Entry Point:** `GET /.well-known/htidp` (The ONLY hardcoded path). Returns the `api_root`.
    * **Root Resource:** Returns links to `handshake_endpoint` (public) and `public_profile` (optional).
    * **The Handshake:** A mechanism to exchange `connection_request` objects.
    * **The Connection Resource:** A unique URL (or endpoint + token) where specific contact data lives.

#### **Phase 2: Core Reference Implementation (Python)**
* **Goal:** A working server that can perform a handshake and serve a vCard.
* **Details:** Implement the "Manager" UI (where the user approves connections) and the "Public" API (where others connect).

#### **Phase 3: The "Unique Connection" Logic & Client**
* **Goal:** Build the PWA that acts as the "Phonebook."
* **Details:** The client must verify signatures and cache data. It must handle the flow of: Scan QR -> POST Request -> Wait for Approval -> Receive Unique Token -> Poll for Data.

#### **Phase 4: Security Layer (Signatures & Keys)**
* **Goal:** Add the crypto-layer.
* **Details:** Exchange public keys during handshake. Sign all updates. Implement "Verified Identity" (e.g., Acme Corp signs Alice's key).

#### **Phase 5: Performance & Portability (Zig)**
* **Goal:** A high-performance, low-resource server implementation.



### **Part 3: The Prompt Series**

Execute these prompts in order. They are designed to be "iterative," where the output of Prompt 1 feeds into Prompt 2.

#### **Prompt 1: Defining the Protocol Specification**
*Goal: Generate the JSON structure and API flow document.*

> **Task:** Draft the **htidp Protocol Specification v0.1**.
>
> **Requirements:**
> 1.  **Discovery:** Define the JSON response for `/.well-known/htidp` and the `api_root`.
> 2.  **Handshake Flow:** Define the `POST` request payload for initiating a connection. It must include the requester's `api_root` and a `nonce`.
> 3.  **Connection Object:** Define the response when a connection is established. This must include a `read_token` and a `subscription_url` where the other party can poll for updates.
> 4.  **Data Model:** Define the structure of a "Profile" using URL-namespaces.
>     * Namespace 1: `htidp.org/core/vcard` (Basic info: Name, Photo).
>     * Namespace 2: `htidp.org/core/security` (Public Keys).
> 5.  **Example:** Provide a full JSON example of a handshake request and a subsequent profile poll response.
>
> **Constraint:** Ensure strict adherence to the "No Hardcoded Paths" rule. Every step must rely on a link provided in the previous response.

#### **Prompt 2: The Python Reference Server (Core)**
*Goal: A basic server that handles the handshake.*

> **Task:** Create a **Python Reference Implementation** using FastAPI.
>
> **Components:**
> 1.  **Data Store:** Use a simple JSON file or SQLite for storage.
> 2.  **Public Endpoints:**
>     * Implement `/.well-known/htidp`.
>     * Implement the `api_root` which provides the `handshake_url`.
>     * Implement the `handshake_url` (accepts POST).
> 3.  **Logic:**
>     * When a POST comes to `handshake_url`, save it as "Pending".
>     * (Mocking the UI): Create a simple administrative route `/admin/approve/{request_id}` that generates a unique `access_token` and returns the callback to the requester.
> 4.  **Private Endpoints:**
>     * Implement a `connection_data_url` that requires the `access_token` and returns the user's vCard data in the htidp format.
>
> **Deliverable:** A single `server.py` file that I can run and test with `curl`.

#### **Prompt 3: The PWA Client (The "Address Book")**
*Goal: A browser-based client that can connect to the server.*

> **Task:** Create the **Reference Client (PWA)** using vanilla HTML/JS (no heavy frameworks).
>
> **Features:**
> 1.  **Local Identity:** The client should act as a "Viewer" for now. It needs a form to input "My Server URL".
> 2.  **Add Contact Flow:**
>     * Input: A target URL (e.g., `alice.com`).
>     * Action: Fetch `alice.com/.well-known/htidp`, find the `handshake_url`, and send a connection request.
> 3.  **Polling:** Once the request is approved (simulate this manually on the server for now), the client should start polling the `subscription_url` provided by the server.
> 4.  **Display:** Render the JSON data (Name, Photo) nicely.
>
> **Requirement:** Use strict Error Handling. If a namespace (URL key) is not understood, the client must simply ignore it and render what it knows.

#### **Prompt 4: Security Extension (Crypto & Web of Trust)**
*Goal: Add signing and verification.*

> **Task:** Extend the Protocol Spec and Python Server to support **Identity Verification**.
>
> **Requirements:**
> 1.  **Key Generation:** On startup, the server must generate an Ed25519 key pair.
> 2.  **Handshake Update:** The handshake request must now be signed by the requester's private key. The payload must include the `public_key`.
> 3.  **Response Update:** The server must verify the signature before marking the request "Pending".
> 4.  **Web of Trust:** Define a new namespace `htidp.org/ext/trust`.
>     * Add a field `verifications`: A list of signatures from other entities (e.g., "My Employer", "My Bank") attesting that "This public key belongs to Alice".
>
> Update the `server.py` to include this signing/verification logic.

#### **Prompt 5: The Zig Implementation (Performance)**
*Goal: High-speed version.*

> **Task:** Port the Python `server.py` logic to **Zig** using the `zap` or `http.zig` library.
>
> **Focus:**
> 1.  Replicate the `/.well-known/htidp` and Handshake logic.
> 2.  Focus on memory safety and concurrency.
> 3.  Ensure the JSON parsing handles the "dynamic URL keys" gracefully (e.g., using a map/hashmap rather than a rigid struct).

#### **Prompt 6: Marketing & Use Cases**
*Goal: Explain "Why htidp?"*

> **Task:** Create content for the project `README.md` and a landing page.
>
> 1.  **Comparison:** Create a table comparing "Phone Numbers", "Facebook Friends", and "htidp". Highlight Privacy, Ownership, and Extensibility.
> 2.  **Visuals:** Describe 3 diagrams I should create (using Mermaid.js or generic description):
>     * **Diagram A:** The "Awkward Handshake" vs. The "htidp Scan".
>     * **Diagram B:** The "Unique Connection" architecture (Alice has 3 different 'faces' for 3 different contacts).
>     * **Diagram C:** The Anti-Spam trust chain.
> 3.  **Pitch:** Write a 1-paragraph "Elevator Pitch" for a developer audience.



