# ScoutIO

Agentic research pipeline built for Composio's take-home assignment. Given
a list of 100 apps, ScoutIO researches each one to determine its auth
method, whether API access is self-serve or gated, its API surface, and
whether it could be an agent toolkit today — then verifies its own
accuracy by sampling results and auditing them against real docs.

**Live case study:** https://scoutio-nivethasre.netlify.app
**Repo:** https://github.com/NivethaSre/scoutio

## Stack

- Python 3.11
- Groq API (`llama-3.3-70b-versatile`) for structured extraction
- Composio SDK + Composio Search toolkit (`COMPOSIO_SEARCH_TOOLS` via
  `session.tools()`) for the research/lookup step
- No database — JSON files for all storage
- Plain HTML/CSS/JS for the deliverable page (no build step)

## Files

| File | Purpose |
|---|---|
| `apps.json` | The 100 apps to research (name + hint URL) |
| `scoutio_agent.py` | Main research agent — runs all 100 apps, saves `results_raw.json` |
| `patterns.py` | Aggregates results into pattern findings, saves `patterns.json` |
| `verify.py` | Interactive verification — re-runs a sample, audits diffs against real docs, saves `verification_log.json` |
| `build_index_html.py` | Builds the final `index.html` from the JSON outputs |
| `index.html` | The deliverable — findings, patterns, agent explanation, verification |

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:
GROQ_API_KEY=your_groq_key
COMPOSIO_API_KEY=your_composio_key

Both have free tiers — no paid plan required.

## How to run the research agent

Run in order:

```bash
python scoutio_agent.py          # researches all 100 apps → results_raw.json
python patterns.py               # finds patterns → patterns.json
python verify.py --sample 10     # audits a sample interactively → verification_log.json
python build_index_html.py       # builds index.html from the above
```

`verify.py` prompts you, per app, to confirm or correct any field where
the re-run pipeline disagrees with the original run — this is the human
audit step, not another automated pass. Open `index.html` afterward, or
view the deployed version at the live link above.

## Accuracy

- Sample: 3 apps (Plaid, Pylon, Attio), 27 fields evaluated
- Initial (raw) agreement between two automated runs: **48.15%** (14 differences)
- After human audit of those differences: **85.19%** accurate
- 0 fields needed an actual ground-truth correction — most flagged
  "differences" were wording/format mismatches (e.g. auth method phrased
  differently), not factual errors
- Takeaway: raw automated re-run comparison understates accuracy; a
  human audit pass is what separates real errors from surface phrasing
  differences

Full per-field diffs: `verification_log.json`. Honest examples of
specific mismatches and what caused them are shown in the verification
section of `index.html`.
