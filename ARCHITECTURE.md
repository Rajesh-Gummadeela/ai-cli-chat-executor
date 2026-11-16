# System Architecture & Technical Specification

## 1. High-Level Architecture Overview

```mermaid
flowchart TD
    User([User Prompt via Browser]) --> UI[Next.js 15 Chat Frontend]
    UI -->|POST /chat| API[FastAPI Backend Engine]

    subgraph Backend Orchestration Layer
        API --> Intent[Intent & Parameter Parser]
        Intent --> URLVal{URL Validator & SSRF Guard}

        URLVal -->|Invalid / Blocked IP| ErrResp[Return Honest Error & Code 2]
        URLVal -->|Safe Public URL| Executor[CLI Subprocess Executor]

        subgraph Real CLI Process Sandbox
            Executor -->|asyncio.create_subprocess_exec| SubProc[Standalone Crawler CLI Binary]
            SubProc -->|HTTP GET Requests| Web[Public Target Website]
            Web -->|HTML Content| SubProc
            SubProc -->|Exit Code, Duration, stderr| Executor
            SubProc -->|JSON Payload on stdout| Executor
        end

        Executor --> OutputParser[CLI Output & JSON Parser]
        OutputParser --> LLM[AI Synthesis Engine\nGemini / OpenAI / Local NLP]
        LLM --> Formatter[Response Formatter]
    end

    Formatter -->|Structured JSON & Summary| UI
    ErrResp -->|Security Alert| UI
```

---

## 2. Core Components

### 2.1 Chat UI Layer (Frontend)
- **Framework:** Next.js 15 (App Router), React 19, TypeScript
- **Styling:** Tailwind CSS v4, custom cyber-dark theme
- **Markdown & Code:** `react-markdown` with `remark-gfm`
- **Key Features:**
  - Real-time execution status stepper (`intent` -> `validate` -> `cli` -> `llm`)
  - Subprocess diagnostics modal (inspect raw stdout/stderr/command)
  - One-click copy and file download for extracted JSON
  - Configurable parameters drawer (max pages, recursion depth, timeout)
  - Quick-start prompt chips for mandatory demo and security tests

### 2.2 API Orchestration Layer (Backend)
- **Framework:** FastAPI with Python 3.11+
- **Endpoints:**
  - `POST /chat` and `POST /api/chat`: Primary conversational CLI execution endpoint
  - `POST /api/chat/stream`: Server-Sent Events (SSE) streaming execution events
  - `POST /api/cli/execute`: Direct CLI execution for developer testing
  - `GET /api/health`: System diagnostics, active AI engine, and whitelist inspection
  - `GET /docs`: Interactive OpenAPI / Swagger UI

### 2.3 Intent Understanding & Parameter Extraction
- Extracts:
  - `url`: Target website URL (supports full URLs and naked domains)
  - `task`: Action type (`crawl_and_summarize`, `extract_json`, etc.)
  - `expected_output`: `summary_and_json`, `json_only`, or `summary_only`
  - `max_pages`: Requested page limit (default: 3, max: 10)
  - `max_depth`: Traversal depth (default: 1, max: 3)
- Supports external LLM extraction with deterministic heuristic fallback when offline.

### 2.4 Security & SSRF Protection
- **Scheme Whitelist:** Only `http` and `https` allowed; blocks `file://`, `ftp://`, `gopher://`, `data://`.
- **IP Address Restriction:**
  - Blocks loopback (`127.0.0.0/8`, `::1`)
  - Blocks RFC 1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`)
  - Blocks link-local (`169.254.0.0/16`)
  - Blocks cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`)
- **DNS Resolution Check:** Resolves domain via `socket.getaddrinfo` to prevent DNS rebinding attacks.

### 2.5 CLI Subprocess Executor (`services/cli_executor.py`)
- **Subprocess Spawning:** Invokes `asyncio.create_subprocess_exec` passing arguments as a list. **Never invokes `shell=True`**, eliminating shell injection vulnerabilities.
- **Binary Whitelist:** Only approved executables (`crawler_cli`, `python`, `playwright`, `crawl4ai`) are permitted.
- **Process Supervision:** Monitors stdout and stderr streams asynchronously.
- **Timeout Enforcement:** Kills child process tree if execution exceeds the configured timeout threshold.

### 2.6 Crawler CLI Tool (`services/crawler_cli.py`)
- Standalone CLI executable with `argparse`.
- Performs real HTTP requests using `httpx.Client(follow_redirects=True)`.
- Parses HTML via `BeautifulSoup4` with script/style decomposition.
- Extracts:
  - Page title, meta description, author, OpenGraph tags
  - Headings hierarchy (H1, H2, H3, H4)
  - Cleaned text content
  - Discovered links (classified into internal vs external)
  - Discovered images and alt tags
- Exit codes:
  - `0`: Success
  - `1`: Unexpected exception
  - `2`: Invalid CLI arguments / malformed URL
  - `3`: Network timeout or connection refusal
  - `4`: HTTP 4xx or 5xx response
  - `5`: Security / SSRF violation

---

## 3. End-to-End Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant Frontend as Next.js Chat UI
    participant Backend as FastAPI /chat
    participant Validator as URL & SSRF Validator
    participant Executor as CLI Executor
    participant Subprocess as Crawler CLI (subprocess)
    participant TargetWeb as Target Website
    participant AI as AI Engine (Gemini / OpenAI / Local)

    User->>Frontend: Enter prompt (e.g. "Crawl https://example.com...")
    Frontend->>Backend: POST /chat { message: "..." }
    Backend->>Backend: Extract intent & target URL
    Backend->>Validator: Validate URL & check DNS/SSRF
    alt URL is restricted (e.g. localhost)
        Validator-->>Backend: Blocked (SSRF protection)
        Backend-->>Frontend: Exit code 2, error message
        Frontend-->>User: Display Security Alert
    else URL is safe
        Validator-->>Backend: Sanitized URL
        Backend->>Executor: run_crawler(url, max_pages=3, timeout=20)
        Executor->>Subprocess: asyncio.create_subprocess_exec(python, crawler_cli.py, ...)
        Subprocess->>TargetWeb: HTTP GET /
        TargetWeb-->>Subprocess: 200 OK (HTML)
        Subprocess->>Subprocess: Parse HTML, extract text, headings, links
        Subprocess-->>Executor: stdout (JSON), stderr (Logs), exitCode: 0
        Executor-->>Backend: CLIExecutionResult
        Backend->>AI: Synthesize summary & structured JSON
        AI-->>Backend: Markdown summary + structured_json
        Backend-->>Frontend: Return ChatResponse payload
        Frontend-->>User: Render summary, JSON viewer, execution diagnostics
    end
```

---

## 4. State Transition Machine

```mermaid
stateDiagram-v2
    [*] --> Idle: Application Ready
    Idle --> InterpretingIntent: User Submits Prompt
    InterpretingIntent --> MissingDetails: No URL Detected
    MissingDetails --> Idle: Request Clarification

    InterpretingIntent --> ValidatingURL: Target URL Extracted
    ValidatingURL --> SecurityRejection: Private IP / SSRF / Malformed
    SecurityRejection --> Idle: Return Exit Code 2 & Error

    ValidatingURL --> SpawningCLI: URL Verified & Safe
    SpawningCLI --> StreamingOutput: Subprocess Running
    StreamingOutput --> ProcessTimeout: Duration > Timeout
    ProcessTimeout --> Idle: Terminate Process & Return Code 124

    StreamingOutput --> ExecutionFailed: Exit Code != 0
    ExecutionFailed --> Idle: Report Error & stderr

    StreamingOutput --> SynthesizingAI: Exit Code == 0 (Valid JSON Captured)
    SynthesizingAI --> ResponseDelivered: Summary & JSON Generated
    ResponseDelivered --> Idle: Ready for Next Request
```
