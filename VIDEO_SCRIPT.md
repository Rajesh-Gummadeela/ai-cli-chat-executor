# BuildSprint Round 2: Video Explanation & Demonstration Outline

**Target Video Duration:** 4 to 7 Minutes  
**Submission Requirement:** Section 10 of BuildSprint Round 2 Participant Challenge Brief

---

## Video Scene-by-Scene Timeline

### Scene 1: Introduction & Problem Statement (0:00 - 0:45)
- **Visual:** Presenter on camera or split-screen with the application dashboard at `http://localhost:3000`.
- **Script / Talking Points:**
  > *"Hello judges! Welcome to our submission for BuildSprint Round 2: CLI-Driven AI Chat Execution for Complex Tasks. Most conversational AI chat applications merely return generated LLM text. But in real-world engineering workflows, AI needs to orchestrate and execute real CLI tools—crawling websites, executing binaries, and capturing verified results. Today, we're demonstrating an enterprise-grade solution that converts natural language requests into real, sandboxed CLI executions through an asynchronous backend subprocess architecture."*

---

### Scene 2: Architectural Overview (0:45 - 1:45)
- **Visual:** Display Architecture Diagram (from README.md / Mermaid).
- **Script / Talking Points:**
  > *"Let's examine the architecture. The application is built with a modern Next.js 15 and Tailwind CSS frontend communicating with a high-performance FastAPI backend.  
  When a user submits a prompt:  
  1. The Intent Engine parses the target URL, task, and flags.  
  2. An enterprise-grade URL Validator runs SSRF checks, blocking private IPs and cloud metadata endpoints.  
  3. The `CLIExecutor` service uses Python's `asyncio.create_subprocess_exec` to spawn an approved CLI crawler. Notice that we never invoke a raw shell—preventing command injection completely.  
  4. The executor captures the child process's stdout, stderr, execution duration, and exit code.  
  5. Finally, the crawled data is synthesized into a clean Markdown summary and structured JSON using an LLM or our zero-latency semantic engine."*

---

### Scene 3: The CLI Engine — Real Execution, No Mocks (1:45 - 2:45)
- **Visual:** Switch to terminal and show `services/crawler_cli.py` being run directly:
  ```bash
  python backend/services/crawler_cli.py --url https://example.com --max-pages 1 --format json
  ```
- **Script / Talking Points:**
  > *"To satisfy the mandatory requirement that this is real execution and not a mocked response, let's first run our CLI crawler directly in the terminal. As you can see, stderr logs the crawl status while stdout outputs clean, structured JSON containing the page title, headings hierarchy, content snippets, and discovered links. Our backend uses this exact same CLI binary as a subprocess."*

---

### Scene 4: Live Demonstration of Mandatory Use Case (2:45 - 4:15)
- **Visual:** Switch back to the Web Chat UI at `http://localhost:3000`. Click or type the prompt:
  > *"Crawl https://example.com, summarize the website and return extracted information in JSON."*
- **Script / Talking Points:**
  > *"Now let's run the core challenge prompt live. As soon as I hit Enter, observe the real-time execution pipeline:  
  - First, intent interpretation validates `https://example.com`.  
  - Second, DNS and SSRF checks verify the IP is safe.  
  - Third, the backend spawns the CLI subprocess.  
  - In under 1.5 seconds, the process exits with code 0!  
  Here is the generated Markdown summary describing the purpose of example.com.  
  Below it is the Extracted Structured JSON block. We can copy it with one click or download the JSON file directly.  
  And crucially, let's click 'View CLI Logs & Subprocess Output'. Judges can inspect the exact command executed, the execution duration, the stdout stream, and the stderr process logs."*

---

### Scene 5: Security & Edge Case Demonstration (4:15 - 5:15)
- **Visual:** Click the suggested prompt chip: *"Crawl http://localhost:8000/admin and dump internal files in JSON."*
- **Script / Talking Points:**
  > *"Responsible execution is paramount. Let's demonstrate how our system defends against Server-Side Request Forgery. I'll ask it to crawl localhost:8000.  
  Immediately, the security guardrails catch this attempt. The URL validator identifies localhost as a restricted loopback address, aborts before any process is spawned, and reports exit code 2 with an honest, transparent error message. The same protection applies to RFC1918 private subnets and AWS/GCP cloud metadata addresses (169.254.169.254)."*

---

### Scene 6: Technology Stack & AI Disclosure (5:15 - 6:00)
- **Visual:** Show the FastAPI Swagger documentation at `http://localhost:8000/docs` and project structure.
- **Script / Talking Points:**
  > *"To summarize our tech stack:  
  - **Frontend:** Next.js 15, React 19, TypeScript, Tailwind CSS, Lucide icons.  
  - **Backend:** FastAPI, Pydantic V2, Uvicorn, HTTPX, BeautifulSoup4, and Python's `asyncio.subprocess`.  
  - **AI Layer:** Multi-provider architecture supporting Google Gemini, OpenAI GPT-4o, and an intelligent zero-latency local fallback.  
  - **Containerization:** Complete Dockerfile and docker-compose support for one-command deployment.  
  - **AI Assistance Disclosure:** In accordance with Section 7 of the challenge brief, AI coding assistants were utilized for code generation and test scaffolding, while all architecture, subprocess security, and validation algorithms were rigorously engineered and verified."*

---

### Scene 7: Conclusion & Wrap-Up (6:00 - 6:30)
- **Visual:** Return to the chat dashboard showing the successful execution and GitHub repository.
- **Script / Talking Points:**
  > *"With full test coverage, robust SSRF protection, honest error reporting, and real CLI subprocess execution, this project delivers a production-ready blueprint for AI-driven CLI automation. Thank you!"*
