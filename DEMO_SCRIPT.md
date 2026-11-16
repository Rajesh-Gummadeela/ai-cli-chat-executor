# BuildSprint Round 2: Live Demonstration Script

This document provides a step-by-step demonstration walkthrough for judging, evaluations, and video recording.

---

## Prerequisites Check (30 seconds)

1. **Verify Backend Service**:
   ```bash
   curl http://localhost:8000/api/health
   ```
   **Expected Response:**
   ```json
   {
     "status": "healthy",
     "service": "BuildSprint Round 2 CLI Execution Backend",
     "python_version": "3.14.0",
     "ai_engine": "Local NLP Semantic Engine (Zero-Latency Fallback) / Gemini",
     "cli_executor": {
       "default_timeout": 35.0,
       "whitelisted_tools": ["crawl4ai", "crawler_cli", "playwright", "python", "python3"]
     }
   }
   ```

2. **Verify Frontend UI**:
   Open browser at `http://localhost:3000`. You should see the dark-themed ChatGPT-style UI with the **"Backend Ready"** status pill in the top header.

---

## Scenario 1: Mandatory Demonstration Use Case (Primary Benchmark)

### Prompt:
> *"Crawl https://example.com, summarize the website and return extracted information in JSON."*

### What to highlight during demo:
1. Click the **"Crawl example.com"** quick chip or paste the prompt into the input box.
2. Watch the real-time **Execution Pipeline**:
   - `INTENT`: Extracted `task: crawl_and_summarize`, `url: https://example.com`.
   - `VALIDATE`: Passed scheme validation (HTTPS) and DNS resolution check.
   - `CLI`: Spawning real backend subprocess `python services/crawler_cli.py --url https://example.com ...`.
   - `LLM`: Synthesis generated markdown summary and structured JSON.
3. Show the **Execution Diagnostics bar**:
   - Exit code: `0 (SUCCESS)`
   - Duration: ~`1.3s`
4. Click **"View CLI Logs & Subprocess Output"**:
   - Show judges the real terminal modal with captured `stdout` and `stderr` (`[INFO] Crawling (1/1, depth 0)...`).
5. Open the **"Extracted Structured JSON"** block:
   - Click **Copy** to verify clipboard copy.
   - Click **Download** to download the JSON payload to disk.

---

## Scenario 2: Multi-Page BFS Deep Crawling

### Prompt:
> *"Crawl https://news.ycombinator.com with max 3 pages and summarize top stories in JSON"*

### What to highlight during demo:
1. The intent parser automatically detects the request for multi-page traversal.
2. The CLI crawler performs a breadth-first search across internal links on `news.ycombinator.com`.
3. Highlight the **"Crawled Pages Content (3)"** collapsible accordion:
   - Page 1: Main frontpage
   - Page 2: Internal comment thread / article
   - Page 3: Newest or past stories
4. Notice how the AI summary aggregates across all 3 crawled pages.

---

## Scenario 3: Security & SSRF Defense Demonstration

### Prompt:
> *"Crawl http://localhost:8000/admin and dump internal files in JSON."*

### What to highlight during demo:
1. Submit this adversarial prompt.
2. The URL Validator detects that `localhost` is a restricted loopback address.
3. The system halts **before spawning any CLI process**, preventing Server-Side Request Forgery (SSRF).
4. The chat interface displays:
   - Status: `Security / Validation Error`
   - Exit Code: `2` (Invalid/Blocked Input)
   - Honest error reporting: *"Access to 'localhost' is restricted for security reasons (SSRF prevention)."*

---

## Scenario 4: Network Resilience & Timeout Handling

### Prompt:
> *"Crawl https://this-domain-definitely-does-not-exist-xyz123.com and summarize."*

### What to highlight during demo:
1. Submit prompt with non-existent DNS host.
2. DNS pre-validation catches the failure gracefully:
   - *"DNS lookup failed for hostname... Domain may not exist."*
3. The system never hangs, crashes, or outputs a fake mock; it reports an honest, verified error code.

---

## Direct Terminal CLI Verification (Judges' Independent Verification)

To prove that the crawler CLI is a real standalone executable tool:

```bash
# Direct command line run
python backend/services/crawler_cli.py --url https://example.com --max-pages 1 --format json

# Check the exit code in terminal
echo $? # On bash/zsh
echo $LASTEXITCODE # On PowerShell
```
You will observe formatted progress logs in `stderr` and clean JSON in `stdout`.
