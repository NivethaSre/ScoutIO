"""
ScoutIO Verification Script (verify.py)
--------------------------------------
Verification and audit tool for testing pipeline reproducibility and accuracy.

Features:
1. Samples N apps (default 10, configurable via --sample CLI argument).
2. Performs real re-runs using Composio Search + Groq LLM pipeline when API keys are available.
3. If API keys are missing, clearly reports that live verification cannot run without faking data.
4. Programmatically compares Run 1 (results_raw.json) against Run 2 across all audit fields.
5. In interactive mode, allows the user to audit fields, mark incorrect values, and record ground-truth corrections.
6. In non-interactive mode, performs automated discrepancy detection without fabricating human corrections.
7. Calculates initial agreement/accuracy and audited accuracy.
8. Persists newly generated audit data to verification_log.json.
"""

import os
import sys
import json
import random
import argparse
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

from scoutio_agent import (
    initialize_composio_session,
    search_app_documentation,
    extract_app_metadata,
    INPUT_FILE,
    OUTPUT_FILE
)

MODEL_NAME = "openai/gpt-oss-120b"
VERIFY_LOG_FILE = "verification_log.json"

AUDIT_FIELDS = [
    "category",
    "one_liner",
    "auth_methods",
    "access",
    "api_surface",
    "mcp_exists",
    "buildability_verdict",
    "blocker",
    "evidence_url"
]


def parse_args():
    parser = argparse.ArgumentParser(description="ScoutIO Verification and Accuracy Auditing Tool")
    parser.add_argument(
        "--sample", "-n",
        type=int,
        default=10,
        help="Number of apps to randomly sample for verification (default: 10)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)"
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run non-interactively using programmatic comparison without human prompts"
    )
    return parser.parse_args()


def load_data(filepath: str) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []


def are_fields_different(val1: Any, val2: Any, field_name: str) -> bool:
    """
    Programmatically compares two field values to detect differences between Run 1 and Run 2.
    """
    if val1 is None and val2 is None:
        return False
    if val1 is None or val2 is None:
        return True

    # List of auth methods (case-insensitive set comparison)
    if field_name == "auth_methods":
        list1 = [str(x).strip().lower() for x in (val1 if isinstance(val1, list) else [val1])]
        list2 = [str(x).strip().lower() for x in (val2 if isinstance(val2, list) else [val2])]
        return set(list1) != set(list2)

    # Boolean field (mcp_exists)
    if field_name == "mcp_exists":
        def to_bool_flag(v):
            if isinstance(v, bool):
                return v
            if str(v).lower() in ("true", "yes", "1"):
                return True
            if str(v).lower() in ("false", "no", "0"):
                return False
            return "unknown"
        return to_bool_flag(val1) != to_bool_flag(val2)

    # Categorical classification fields (case-insensitive normalized)
    if field_name in ("access", "buildability_verdict", "category"):
        return str(val1).strip().lower() != str(val2).strip().lower()

    # Text fields: one_liner, api_surface, blocker, evidence_url
    s1 = str(val1).strip().lower()
    s2 = str(val2).strip().lower()
    return s1 != s2


async def rerun_app(session, app_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Re-runs an app through the real Composio Search + Groq extraction pipeline."""
    app_name = app_meta["app"]
    hint_url = app_meta.get("hint_url", "")

    try:
        search_ctx = await search_app_documentation(session, app_name, hint_url)
        fresh_result = await extract_app_metadata(app_meta, search_ctx)
        fresh_result["app"] = app_name
        return fresh_result
    except Exception as e:
        return {
            "app": app_name,
            "error": str(e)
        }


def format_field(val: Any) -> str:
    """Helper to format fields cleanly for side-by-side terminal display."""
    if val is None:
        return "None"
    if isinstance(val, list):
        return ", ".join(str(x) for x in val)
    return str(val)


def print_side_by_side(app_name: str, run1: Dict[str, Any], run2: Dict[str, Any], diff_fields: List[str]):
    """Displays a clean side-by-side terminal comparison with differences marked."""
    print("\n" + "=" * 90)
    print(f"APP: {app_name.upper()}  (Differences: {len(diff_fields)})")
    print("=" * 90)
    print(f"{'FIELD':<22} | {'ORIGINAL RUN (Run 1)':<31} | {'VERIFICATION RUN (Run 2)':<31}")
    print("-" * 90)

    for field in AUDIT_FIELDS:
        val1 = format_field(run1.get(field))
        val2 = format_field(run2.get(field))

        str1 = (val1[:28] + "...") if len(val1) > 31 else val1
        str2 = (val2[:28] + "...") if len(val2) > 31 else val2

        diff_marker = "* " if field in diff_fields else "  "
        print(f"{diff_marker}{field:<20} | {str1:<31} | {str2:<31}")
    print("-" * 90)


async def main():
    args = parse_args()
    print("=" * 80)
    print("ScoutIO Verification & Audit Pipeline")
    print("=" * 80)

    groq_key = os.getenv("GROQ_API_KEY", "").strip()
    composio_key = os.getenv("COMPOSIO_API_KEY", "").strip()

    # Strict check: Never fabricate results when API keys are missing
    if not groq_key or not composio_key:
        print("[ERROR] Live verification cannot start because a required API key is missing.")
        if not groq_key:
            print("  - GROQ_API_KEY is missing. Add it to the .env file.")
        if not composio_key:
            print("  - COMPOSIO_API_KEY is missing. Add it to the .env file.")

        # Save an honest unverified status report to verification_log.json
        unverified_log = {
            "status": "unverified",
            "error": "Missing GROQ_API_KEY and/or COMPOSIO_API_KEY. Live verification could not run.",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sample_size": 0,
            "fields_evaluated": 0,
            "differences_found": 0,
            "initial_accuracy_percent": None,
            "human_corrections_count": 0,
            "audited_accuracy_percent": None,
            "audit_records": []
        }
        with open(VERIFY_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(unverified_log, f, indent=2, ensure_ascii=False)
        print(f"[INFO] '{VERIFY_LOG_FILE}' newly written with unverified status (no mock data generated).")
        sys.exit(1)

    # Load input data
    apps_list = load_data(INPUT_FILE)
    results_raw = load_data(OUTPUT_FILE)

    if not apps_list:
        print(f"[FATAL] Input file '{INPUT_FILE}' not found or empty. Aborting.")
        sys.exit(1)
    if not results_raw:
        print(f"[FATAL] Baseline results file '{OUTPUT_FILE}' not found or empty. Run scoutio_agent.py first.")
        sys.exit(1)

    results_map = {item.get("app"): item for item in results_raw if "app" in item}

    # Sample N apps
    sample_size = min(max(1, args.sample), len(apps_list))
    rng = random.Random(args.seed)
    sampled_apps = rng.sample(apps_list, sample_size)

    print(f"[INFO] Sampled {sample_size} apps (seed={args.seed}): {', '.join(a['app'] for a in sampled_apps)}")
    print(f"[INFO] Initializing Composio session (user_id='scoutio') and Groq client ({MODEL_NAME})...")

    session = initialize_composio_session()

    is_interactive = not args.non_interactive and sys.stdin.isatty()
    audit_records = []
    total_fields_evaluated = 0
    total_differences_found = 0
    total_human_corrections = 0
    total_human_incorrect = 0

    for idx, app_meta in enumerate(sampled_apps, 1):
        app_name = app_meta["app"]
        print(f"\n[{idx}/{sample_size}] Re-running pipeline for '{app_name}'...")

        original_run = results_map.get(app_name, {})
        fresh_run = await rerun_app(session, app_meta)

        # Detect differences programmatically
        differences = []
        if "error" in fresh_run:
            print(f"  [WARNING] Run 2 encountered an error: {fresh_run['error']}")
            differences = list(AUDIT_FIELDS)
        else:
            for field in AUDIT_FIELDS:
                if are_fields_different(original_run.get(field), fresh_run.get(field), field):
                    differences.append(field)

        total_fields_evaluated += len(AUDIT_FIELDS)
        total_differences_found += len(differences)

        # Print side-by-side comparison
        print_side_by_side(app_name, original_run, fresh_run, differences)

        corrections_for_app = {}
        incorrect_fields_for_app = []

        if is_interactive:
            print(f"Automated differences detected: {', '.join(differences) if differences else 'None'}")
            print("Enter comma-separated WRONG fields in Run 2 to audit (or press ENTER to accept automated differences):")
            try:
                user_input = input("Wrong fields: ").strip()
            except (EOFError, KeyboardInterrupt):
                user_input = ""

            if user_input:
                user_wrong = [f.strip() for f in user_input.split(",") if f.strip() in AUDIT_FIELDS]
                incorrect_fields_for_app = user_wrong
            else:
                incorrect_fields_for_app = list(differences)

            # Prompt for corrections
            for field in incorrect_fields_for_app:
                try:
                    corr_val = input(f"  Enter ground-truth correction for '{field}' (or press ENTER to skip): ").strip()
                except (EOFError, KeyboardInterrupt):
                    corr_val = ""
                if corr_val:
                    corrections_for_app[field] = corr_val

            total_human_corrections += len(corrections_for_app)
            total_human_incorrect += len(incorrect_fields_for_app)
        else:
            # Non-interactive mode: use programmatic differences directly
            incorrect_fields_for_app = list(differences)

        app_agreement_pct = round(((len(AUDIT_FIELDS) - len(differences)) / len(AUDIT_FIELDS)) * 100, 2)
        record = {
            "app": app_name,
            "original_run": original_run,
            "verification_run": fresh_run,
            "differences": differences,
            "agreement_percent": app_agreement_pct,
            "incorrect_fields": incorrect_fields_for_app,
            "corrections": corrections_for_app
        }
        audit_records.append(record)

    # Compute overall summary metrics
    initial_agreement_pct = round(
        ((total_fields_evaluated - total_differences_found) / total_fields_evaluated) * 100, 2
    ) if total_fields_evaluated > 0 else 0.0

    audited_accuracy_pct = None
    if is_interactive:
        audited_correct = total_fields_evaluated - total_human_incorrect
        audited_accuracy_pct = round((audited_correct / total_fields_evaluated) * 100, 2) if total_fields_evaluated > 0 else 0.0

    # Save freshly generated verification log
    verification_payload = {
        "status": "completed",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": "interactive" if is_interactive else "non-interactive",
        "sample_size": sample_size,
        "fields_evaluated": total_fields_evaluated,
        "differences_found": total_differences_found,
        "initial_accuracy_percent": initial_agreement_pct,
        "human_corrections_count": total_human_corrections if is_interactive else 0,
        "audited_accuracy_percent": audited_accuracy_pct,
        "audit_records": audit_records
    }

    with open(VERIFY_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(verification_payload, f, indent=2, ensure_ascii=False)

    print(f"\n[SUCCESS] Fresh verification log written to '{VERIFY_LOG_FILE}'.")

    # Final concise summary
    print("\n" + "=" * 50)
    print("Verification complete")
    print(f"Apps sampled: {sample_size}")
    print(f"Fields evaluated: {total_fields_evaluated}")
    print(f"Differences found: {total_differences_found}")
    print(f"Initial agreement/accuracy: {initial_agreement_pct:.2f}%")
    if is_interactive:
        print(f"Human corrections: {total_human_corrections}")
        print(f"Audited accuracy: {audited_accuracy_pct:.2f}%")
    else:
        print("Human corrections: 0 (not performed in non-interactive mode)")
        print("Audited accuracy: Human audit not performed yet")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
