"""
ScoutIO Research Agent (scoutio_agent.py)
----------------------------------------
Autonomous research agent for evaluating developer API access across 100 SaaS applications.

Stack:
- Python 3.11+ with asyncio for concurrency
- Composio SDK (session user_id="scoutio", COMPOSIO_SEARCH_TOOLS) for discovering official docs
- Groq API (openai/gpt-oss-120b via OpenAI-compatible client) for structured JSON extraction
- asyncio.Semaphore(8) for controlling concurrency
- Robust retry logic (retry once on failure, isolate errors to never crash the batch)
- Real-time incremental persistence to results_raw.json
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

# ==============================================================================
# 1. API CONFIGURATION & CLIENT INITIALIZATION
# ==============================================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")

# We use the official OpenAI-compatible async client pointing to Groq's endpoint.
from openai import AsyncOpenAI

client = (
    AsyncOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY,
    )
    if GROQ_API_KEY
    else None
)

MODEL_NAME = "openai/gpt-oss-120b"
CONCURRENCY_LIMIT = 8
INPUT_FILE = "apps.json"
OUTPUT_FILE = "results_raw.json"

# Lock for safely writing results incrementally to results_raw.json across concurrent tasks
file_write_lock = asyncio.Lock()


# ==============================================================================
# 2. COMPOSIO SEARCH TOOLKIT INTEGRATION
# ==============================================================================

def initialize_composio_session():
    """
    Initializes the Composio client and creates a scoped session for 'scoutio'.
    
    Why Composio Sessions?
    - A Composio Session scopes tool discovery, authentication, and execution to a specific user.
    - COMPOSIO_SEARCH_TOOLS is a meta-tool inside the session that allows dynamic discovery
      of documentation, developer endpoints, and toolkits without cluttering the LLM's context.
    """
    if not COMPOSIO_API_KEY:
        raise RuntimeError("COMPOSIO_API_KEY is missing. Add it to the .env file.")

    try:
        from composio import Composio
        composio = Composio(api_key=COMPOSIO_API_KEY)
        session = composio.create(user_id="scoutio")
        session.tools()
        print(f"[INFO] Composio session initialized successfully (Session ID: {session.session_id}).")
        return session
    except Exception as e:
        error_text = str(e).replace(COMPOSIO_API_KEY, "[REDACTED]")
        if "401" in error_text or "invalid api key" in error_text.lower():
            raise RuntimeError("Composio returned 401: COMPOSIO_API_KEY is invalid.") from e
        raise RuntimeError(f"Could not initialize Composio session: {error_text}") from e


async def search_app_documentation(session, app_name: str, hint_url: str) -> str:
    """
    Uses the Composio Search toolkit (COMPOSIO_SEARCH_TOOLS) via session.tools()
    and session.execute()
    to find official API developer documentation, authentication guides, and MCP status.
    """
    query = f"{app_name} API documentation developer credentials authentication MCP server"

    if session is None:
        raise RuntimeError("Composio session is not initialized; research cannot continue.")

    try:
        await asyncio.to_thread(session.tools)
        response = await asyncio.to_thread(
            session.execute,
            "COMPOSIO_SEARCH_TOOLS",
            arguments={"queries": [{"use_case": query}]}
        )
        response_error = getattr(response, "error", None)
        if response_error:
            raise RuntimeError(str(response_error))
        data = getattr(response, "data", None)
        if data is None:
            raise RuntimeError("Composio Search returned no data.")
        return json.dumps(data) if isinstance(data, (dict, list)) else str(data)
    except Exception as err:
        error_text = str(err).replace(COMPOSIO_API_KEY, "[REDACTED]")
        if "401" in error_text or "invalid api key" in error_text.lower():
            raise RuntimeError("Composio Search returned 401: COMPOSIO_API_KEY is invalid.") from err
        raise RuntimeError(f"Composio Search failed: {error_text}") from err


# ==============================================================================
# 3. LLM PROMPT & STRUCTURED EXTRACTION
# ==============================================================================

# Strict system prompt instructing the model to adhere strictly to JSON output
SYSTEM_PROMPT = """You are ScoutIO, an expert API research analyst for AI agent toolkits.
Your mission is to evaluate SaaS and developer platforms for agent integration feasibility.

Given the application name, category, hint URL, and developer documentation search results,
determine the exact technical specifications and return ONLY a valid JSON object matching this schema:

{
  "app": "<App Name>",
  "category": "<Category>",
  "one_liner": "<Precise 1-sentence description of the app's core utility>",
  "auth_methods": ["<List of auth methods, e.g. 'OAuth2', 'API Key', 'Bearer Token', 'Basic Auth', 'Cookie / Session'>"],
  "access": "<'self_serve' | 'gated' | 'unclear'>",
  "api_surface": "<Description of API surface, e.g. 'REST (broad: 100+ endpoints)', 'GraphQL (full access)', 'REST (minimal: webhooks only)'>",
  "mcp_exists": <true | false | "unknown">,
  "buildability_verdict": "<'yes' | 'no' | 'partial'>",
  "blocker": <"<Reason for failure or limitation, e.g. 'Requires Enterprise plan', 'No public API available', 'Mandatory sales/admin review'>" | null>,
  "evidence_url": "<The exact documentation URL or official portal used to substantiate this answer>"
}

DEFINITIONS FOR CLASSIFICATION:
1. access:
   - "self_serve": Any developer can sign up for free or start a self-serve trial immediately to get API credentials without speaking to sales or waiting for manual enterprise review.
   - "gated": API access requires an enterprise/paid upgrade, manual admin review, partner verification, or sales outreach.
   - "unclear": Documentation does not clearly specify access barriers.
2. buildability_verdict:
   - "yes": Can be built into an autonomous agent toolkit today with standard self-serve API keys or OAuth2.
   - "no": Cannot be integrated today (e.g. no public API, strict enterprise gatekeeper, invite-only).
   - "partial": Possible, but severely constrained (e.g. read-only endpoints, strict rate limits, or missing crucial actions).
3. blocker:
   - Must be null if buildability_verdict is "yes".
   - Must provide the concise primary blocker reason if verdict is "no" or "partial".

CRITICAL: Output ONLY valid raw JSON. No markdown code blocks, no preamble, no postscript.
"""


async def extract_app_metadata(app_info: Dict[str, Any], search_context: str) -> Dict[str, Any]:
    """
    Sends the gathered documentation evidence to Groq's openai/gpt-oss-120b
    and parses the strictly formatted JSON response.
    """
    if client is None:
        raise RuntimeError("GROQ_API_KEY is missing. Add it to the .env file.")

    user_prompt = f"""Application: {app_info['app']}
Category: {app_info.get('category', 'Uncategorized')}
Hint URL: {app_info.get('hint_url', '')}

Research & Search Evidence:
{search_context}

Analyze the application above and return the required JSON object.
"""

    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,  # Low temperature for factual consistency
        response_format={"type": "json_object"}
    )
    
    raw_content = response.choices[0].message.content.strip()
    return json.loads(raw_content)


# ==============================================================================
# 4. RETRY LOGIC & FAULT ISOLATION
# ==============================================================================

async def process_single_app(
    session,
    app_info: Dict[str, Any],
    semaphore: asyncio.Semaphore,
    progress_counter: Dict[str, int],
    total_apps: int
) -> Dict[str, Any]:
    """
    Processes a single application within the concurrency limit:
    1. Acquires semaphore slot (up to 8 concurrent apps).
    2. Searches docs via Composio.
    3. Calls Groq LLM with strict prompt.
    4. Retries ONCE on failure.
    5. On second failure, isolates the error into {"app": name, "error": str(err)}
       so the rest of the batch continues unhindered.
    6. Appends result incrementally to results_raw.json.
    """
    app_name = app_info["app"]

    async with semaphore:
        # ATTEMPT 1
        try:
            search_context = await search_app_documentation(session, app_name, app_info.get("hint_url", ""))
            result = await extract_app_metadata(app_info, search_context)
            # Ensure app key matches exactly
            result["app"] = app_name
        except Exception as first_error:
            # ATTEMPT 2 (RETRY ONCE)
            await asyncio.sleep(1.0)  # Brief backoff before retry
            try:
                search_context = await search_app_documentation(session, app_name, app_info.get("hint_url", ""))
                result = await extract_app_metadata(app_info, search_context)
                result["app"] = app_name
            except Exception as second_error:
                # Second failure: never crash the batch; capture the error record cleanly
                result = {
                    "app": app_name,
                    "category": app_info.get("category", "Unknown"),
                    "error": f"Attempt 1: {str(first_error)} | Attempt 2: {str(second_error)}"
                }

        # Safe incremental persistence to disk
        async with file_write_lock:
            progress_counter["completed"] += 1
            current_count = progress_counter["completed"]
            
            # Read existing results, update or append, and write back
            current_results = []
            if os.path.exists(OUTPUT_FILE):
                try:
                    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                        current_results = json.load(f)
                except Exception:
                    current_results = []
            
            # Replace existing or append
            updated = False
            for i, item in enumerate(current_results):
                if item.get("app") == app_name:
                    current_results[i] = result
                    updated = True
                    break
            if not updated:
                current_results.append(result)

            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(current_results, f, indent=2, ensure_ascii=False)

            status = "done" if "error" not in result else "ERROR"
            print(f"[{current_count}/{total_apps}] {app_name}: {status}")

        return result


# ==============================================================================
# 5. BATCH ORCHESTRATION & MAIN ENTRYPOINT
# ==============================================================================

async def main():
    print("=" * 70)
    print("ScoutIO: Autonomous API Research Agent")
    print("=" * 70)

    if not GROQ_API_KEY:
        print("[FATAL] GROQ_API_KEY is missing. Add it to the .env file.")
        sys.exit(1)
    if not COMPOSIO_API_KEY:
        print("[FATAL] COMPOSIO_API_KEY is missing. Add it to the .env file.")
        sys.exit(1)

    if not os.path.exists(INPUT_FILE):
        print(f"[FATAL] Input file '{INPUT_FILE}' not found. Please create apps.json first.")
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        apps = json.load(f)

    total_apps = len(apps)
    print(f"[INFO] Loaded {total_apps} apps from {INPUT_FILE}.")
    print(f"[INFO] Running concurrency with asyncio.Semaphore({CONCURRENCY_LIMIT}).")
    print(f"[INFO] Model: {MODEL_NAME} via Groq.")

    # Initialize Composio Session
    composio_session = initialize_composio_session()

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    progress_counter = {"completed": 0}

    # Clean or initialize output file
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

    start_time = asyncio.get_event_loop().time()

    # Launch all tasks concurrently; semaphore throttles active batch to 8
    tasks = [
        process_single_app(composio_session, app, semaphore, progress_counter, total_apps)
        for app in apps
    ]
    results = await asyncio.gather(*tasks)

    elapsed = asyncio.get_event_loop().time() - start_time
    success_count = sum(1 for r in results if "error" not in r)
    error_count = total_apps - success_count

    print("=" * 70)
    print(f"Research Completed in {elapsed:.1f}s!")
    print(f"Total Apps: {total_apps} | Success: {success_count} | Errors: {error_count}")
    print(f"Results successfully saved to '{OUTPUT_FILE}'.")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
