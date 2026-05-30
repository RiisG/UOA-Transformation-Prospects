#!/usr/bin/env python3
"""
UO Athletics Donor Prospect Research Agent
Runs daily to find University of Oregon alumni with $5M+ philanthropic capacity.
"""

import anthropic
import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

PROSPECTS_FILE = Path(__file__).parent.parent / "docs" / "prospects.json"

SYSTEM_PROMPT = """You are a senior philanthropic research analyst specializing in major gift
identification for university athletics programs. You have deep expertise in wealth screening,
donor identification, and prospect research for collegiate athletics. You are thorough, accurate,
and always cite your sources."""

RESEARCH_PROMPT = """Your task today is to identify University of Oregon alumni and supporters
who have the financial capacity to make a philanthropic gift of $5 million or more to
University of Oregon Athletics (the Forever Ducks program).

Use web search extensively to research and find high-capacity prospects. Search for:

1. University of Oregon alumni who appear on Forbes 400, Forbes richest lists, or state wealth rankings
2. UO graduates who recently had major wealth events: company IPOs, acquisitions, executive appointments, real estate deals
3. Known Oregon Ducks boosters or athletics donors with significant wealth
4. Tech executives, finance leaders, real estate developers, and entrepreneurs who attended UO
5. University of Oregon Foundation major donors or advisory board members
6. Oregon alumni featured in business news, profiles, or philanthropy announcements
7. Former UO athletes who went on to significant wealth (pro sports, business)
8. Search terms like: "University of Oregon alumni" + "net worth", "UO Ducks donor",
   "Oregon Ducks booster million", "University of Oregon graduate CEO",
   "UO alumni philanthropist", "Oregon Ducks major gift"

For EACH prospect you identify, research them thoroughly and provide this exact JSON structure:

{
  "name": "Full Name",
  "uo_connection": "Specific UO connection - class year, degree, sport played, etc.",
  "current_role": "Current title and organization",
  "location": "City, State/Country",
  "estimated_net_worth": "Best estimate with range e.g. $75M-$150M",
  "giving_capacity": "Estimated max philanthropic gift capacity for UO Athletics",
  "capacity_rating": "TIER_1_TRANSFORMATIONAL (>$25M), TIER_2_PRINCIPAL ($10-25M), or TIER_3_MAJOR ($5-10M)",
  "wealth_sources": "How they built their wealth - company, industry, events",
  "recent_news": "Most important recent news about them from the last 12 months",
  "athletics_connection": "Any known connection to UO Athletics, sports giving, or stadium/facility gifts",
  "philanthropy_history": "Known charitable giving, foundations, or other major gifts",
  "why_prospect": "2-3 sentences on why this person is a strong UO Athletics prospect",
  "engagement_angle": "Best approach or conversation opener for outreach",
  "urgency_flag": "Any time-sensitive wealth event or opportunity window",
  "sources": ["source1 title and URL", "source2 title and URL"],
  "last_updated": "YYYY-MM-DD",
  "confidence": "HIGH, MEDIUM, or LOW - confidence in the wealth/capacity estimate"
}

Find at least 10 distinct, well-researched prospects. Prioritize quality over quantity.
Only include people with:
- Clear University of Oregon connection (alumni, major donor, athletics booster, former athlete)
- Estimated net worth of $25 million or more (capacity to give $5M+)
- Verifiable information from news or public records

Return ONLY a valid JSON array. No introduction, no explanation, just the JSON array starting with [ and ending with ]."""


def load_existing():
    if PROSPECTS_FILE.exists():
        with open(PROSPECTS_FILE) as f:
            data = json.load(f)
            return data.get("prospects", []), data.get("run_history", [])
    return [], []


def merge_and_save(new_prospects, existing_prospects, run_history):
    existing_by_name = {p["name"].lower().strip(): p for p in existing_prospects}

    added = 0
    updated = 0
    for p in new_prospects:
        key = p["name"].lower().strip()
        if key in existing_by_name:
            existing_by_name[key] = p
            updated += 1
        else:
            existing_by_name[key] = p
            added += 1

    all_prospects = list(existing_by_name.values())

    tier_order = {"TIER_1_TRANSFORMATIONAL": 0, "TIER_2_PRINCIPAL": 1, "TIER_3_MAJOR": 2}
    all_prospects.sort(key=lambda p: tier_order.get(p.get("capacity_rating", "TIER_3_MAJOR"), 3))

    run_entry = {
        "date": str(date.today()),
        "timestamp": datetime.now().isoformat(),
        "prospects_found": len(new_prospects),
        "added": added,
        "updated": updated,
        "total_in_database": len(all_prospects)
    }
    run_history.append(run_entry)
    if len(run_history) > 90:
        run_history = run_history[-90:]

    output = {
        "last_updated": datetime.now().isoformat(),
        "last_run_date": str(date.today()),
        "total_prospects": len(all_prospects),
        "tier_1_count": sum(1 for p in all_prospects if p.get("capacity_rating") == "TIER_1_TRANSFORMATIONAL"),
        "tier_2_count": sum(1 for p in all_prospects if p.get("capacity_rating") == "TIER_2_PRINCIPAL"),
        "tier_3_count": sum(1 for p in all_prospects if p.get("capacity_rating") == "TIER_3_MAJOR"),
        "run_history": run_history,
        "prospects": all_prospects
    }

    PROSPECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Database updated: {len(all_prospects)} total prospects ({added} new, {updated} refreshed)")
    return all_prospects, run_entry


def run_agent():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] UO Athletics Prospect Search starting...")

    existing_prospects, run_history = load_existing()
    existing_names = [p["name"] for p in existing_prospects]

    prompt = RESEARCH_PROMPT
    if existing_names:
        avoid_list = ", ".join(existing_names[:30])
        prompt += f"\n\nNOTE: The following prospects are already in the database. Find NEW people not on this list: {avoid_list}"

    print("Conducting web research (this takes 2-4 minutes)...")

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 20
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    # Use the last text block — the first is a preamble, the last contains the JSON
    result_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result_text = block.text

    if not result_text:
        print("ERROR: No text response from agent")
        sys.exit(1)

    try:
        start = result_text.find("[")
        end = result_text.rfind("]") + 1
        if start < 0 or end <= start:
            print("ERROR: Could not find JSON array in response")
            print("Raw response (first 1000 chars):", result_text[:1000])
            sys.exit(1)

        json_str = result_text[start:end]
        new_prospects = json.loads(json_str)
        print(f"Agent found {len(new_prospects)} prospects")

    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}")
        print("Raw response (first 2000 chars):", result_text[:2000])
        sys.exit(1)

    today = str(date.today())
    for p in new_prospects:
        if "last_updated" not in p or not p["last_updated"]:
            p["last_updated"] = today
        rating = p.get("capacity_rating", "")
        if "TIER_1" in rating:
            p["capacity_rating"] = "TIER_1_TRANSFORMATIONAL"
        elif "TIER_2" in rating:
            p["capacity_rating"] = "TIER_2_PRINCIPAL"
        else:
            p["capacity_rating"] = "TIER_3_MAJOR"

    all_prospects, run_entry = merge_and_save(new_prospects, existing_prospects, run_history)

    print(f"Run complete. {run_entry['added']} new, {run_entry['updated']} updated. Total: {run_entry['total_in_database']}")
    print(f"Tier 1 Transformational (>$25M capacity): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_1_TRANSFORMATIONAL')}")
    print(f"Tier 2 Principal ($10-25M): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_2_PRINCIPAL')}")
    print(f"Tier 3 Major ($5-10M): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_3_MAJOR')}")


if __name__ == "__main__":
    run_agent()
