"""
ScoutIO Patterns Analyzer (patterns.py)
---------------------------------------
Analyzes results_raw.json using standard library collections.Counter (no pandas).

Generates:
1. Count of apps per auth_method
2. Count of self_serve vs gated vs unclear per category
3. Most common blocker values
4. List of apps with buildability_verdict == "no", grouped by blocker
5. Overall summary metrics (total apps, verdicts, MCP existence)
6. Outputs structured findings to patterns.json for index.html consumption
"""

import os
import json
from collections import Counter, defaultdict
from typing import Dict, Any, List

INPUT_FILE = "results_raw.json"
OUTPUT_FILE = "patterns.json"


def load_results(filepath: str) -> List[Dict[str, Any]]:
    """Loads raw research results from disk."""
    if not os.path.exists(filepath):
        print(f"[ERROR] Results file '{filepath}' does not exist. Run scoutio_agent.py first.")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_patterns(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Computes summary patterns using collections.Counter without third-party libraries.
    """
    total_apps = len(data)
    valid_apps = [app for app in data if "error" not in app]
    error_apps = [app for app in data if "error" in app]

    # 1. Count of apps per auth_method
    # An app can support multiple auth methods (e.g. OAuth2 and API Key)
    auth_counter = Counter()
    for item in valid_apps:
        methods = item.get("auth_methods", [])
        if isinstance(methods, list):
            for m in methods:
                auth_counter[m.strip()] += 1
        elif isinstance(methods, str):
            auth_counter[methods.strip()] += 1

    # 2. Count of self_serve vs gated per category
    category_access_counts = defaultdict(Counter)
    categories_all = set()
    for item in valid_apps:
        cat = item.get("category", "Uncategorized")
        access = item.get("access", "unclear").lower()
        categories_all.add(cat)
        category_access_counts[cat][access] += 1

    # Convert defaultdict to regular dict for JSON export
    category_access_summary = {
        cat: {
            "self_serve": category_access_counts[cat].get("self_serve", 0),
            "gated": category_access_counts[cat].get("gated", 0),
            "unclear": category_access_counts[cat].get("unclear", 0),
            "total": sum(category_access_counts[cat].values())
        }
        for cat in sorted(categories_all)
    }

    # 3. Most common blocker values
    blocker_counter = Counter()
    for item in valid_apps:
        blocker = item.get("blocker")
        if blocker:
            # Normalize whitespace/case for clean grouping
            clean_blocker = blocker.strip()
            blocker_counter[clean_blocker] += 1

    # 4. List of apps with buildability_verdict "no", grouped by blocker
    no_verdict_apps_by_blocker = defaultdict(list)
    no_verdict_count = 0
    verdict_counter = Counter()
    mcp_counter = Counter()

    for item in valid_apps:
        verdict = str(item.get("buildability_verdict", "unknown")).lower()
        verdict_counter[verdict] += 1

        mcp = item.get("mcp_exists", "unknown")
        mcp_key = "yes" if mcp is True else ("no" if mcp is False else "unknown")
        mcp_counter[mcp_key] += 1

        if verdict == "no":
            no_verdict_count += 1
            blk = item.get("blocker") or "Unspecified Blocker"
            no_verdict_apps_by_blocker[blk.strip()].append({
                "app": item.get("app"),
                "category": item.get("category"),
                "evidence_url": item.get("evidence_url", "")
            })

    # Prepare complete payload
    patterns_payload = {
        "summary": {
            "total_analyzed": total_apps,
            "valid_records": len(valid_apps),
            "error_records": len(error_apps),
            "verdicts": dict(verdict_counter),
            "mcp_existence": dict(mcp_counter)
        },
        "auth_methods": dict(auth_counter.most_common()),
        "category_access": category_access_summary,
        "top_blockers": dict(blocker_counter.most_common(10)),
        "no_verdict_by_blocker": dict(no_verdict_apps_by_blocker)
    }

    return patterns_payload


def print_patterns(patterns: Dict[str, Any]):
    """Pretty-prints analysis metrics to the CLI."""
    summary = patterns["summary"]
    print("\n" + "=" * 75)
    print("SCOUTIO PATTERNS & INSIGHTS REPORT")
    print("=" * 75)
    print(f"Total Applications Analyzed: {summary['total_analyzed']}")
    print(f"Valid Evaluations: {summary['valid_records']} | Errors: {summary['error_records']}")
    print(f"Buildability Verdicts: {summary['verdicts']}")
    print(f"MCP Server Availability: {summary['mcp_existence']}")

    print("\n" + "-" * 75)
    print("1. AUTHENTICATION METHODS DISTRIBUTION")
    print("-" * 75)
    print(f"{'Auth Method':<35} | {'Count':<10}")
    print("-" * 75)
    for auth, count in patterns["auth_methods"].items():
        print(f"{auth:<35} | {count:<10}")

    print("\n" + "-" * 75)
    print("2. DEVELOPER ACCESS BY CATEGORY (SELF-SERVE VS GATED)")
    print("-" * 75)
    print(f"{'Category':<35} | {'Self-Serve':<10} | {'Gated':<8} | {'Total':<6}")
    print("-" * 75)
    for cat, stats in patterns["category_access"].items():
        print(f"{cat:<35} | {stats['self_serve']:<10} | {stats['gated']:<8} | {stats['total']:<6}")

    print("\n" + "-" * 75)
    print("3. MOST COMMON AGENT INTEGRATION BLOCKERS")
    print("-" * 75)
    print(f"{'Blocker Reason':<55} | {'Count':<8}")
    print("-" * 75)
    for blk, count in patterns["top_blockers"].items():
        print(f"{blk[:53]:<55} | {count:<8}")

    print("\n" + "-" * 75)
    print("4. APPS WITH VERDICT 'NO' (GROUPED BY BLOCKER)")
    print("-" * 75)
    for blk, apps in patterns["no_verdict_by_blocker"].items():
        print(f"\n* Blocker: {blk} ({len(apps)} apps)")
        for a in apps:
            print(f"    - {a['app']} ({a['category']})")

    print("\n" + "=" * 75 + "\n")


def main():
    data = load_results(INPUT_FILE)
    if not data:
        return

    patterns = analyze_patterns(data)
    print_patterns(patterns)

    # Save to patterns.json
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(patterns, f, indent=2, ensure_ascii=False)

    print(f"[SUCCESS] Patterns saved to '{OUTPUT_FILE}' for web dashboard visualization.")


if __name__ == "__main__":
    main()
