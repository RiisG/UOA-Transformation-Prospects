#!/usr/bin/env python3
"""
UO Athletics Donor Prospect Research Agent
Runs daily to find University of Oregon alumni with $5M+ philanthropic capacity.
"""

import anthropic
import json
import os
import random
import sys
from datetime import datetime, date
from pathlib import Path

PROSPECTS_FILE = Path(__file__).parent.parent / "docs" / "prospects.json"

SYSTEM_PROMPT = """You are a senior philanthropic research analyst specializing in major gift
identification for university athletics programs. You have deep expertise in wealth screening,
donor identification, and prospect research for collegiate athletics. Your mission is to surface
hidden, undiscovered philanthropic capacity — people who HAVE NOT yet made transformational gifts
but absolutely could. You are thorough, accurate, and always cite your sources."""

RESEARCH_PROMPT = """Your task is to identify UNDISCOVERED University of Oregon alumni and supporters
who have the financial capacity to make a transformational philanthropic gift to University of Oregon
Athletics (the Forever Ducks program) — but have NOT yet done so.

CRITICAL FILTER: Do NOT include people already known as major UO Athletics donors (e.g. Phil Knight,
Penny Knight, Bob Bellotti, Pat Kilkenny). Focus entirely on prospects with HIGH capacity who have
NOT made a transformational gift to UO Athletics. We want to find people before anyone else does.

Use web search extensively. Dig deep. Search for:

1. UO alumni on Forbes 400, state wealth rankings, or regional business journals who have NO known
   UO Athletics giving history
2. UO graduates who recently had major liquidity events (IPO, acquisition, exit, executive comp
   disclosures) and have not yet been cultivated by UO Athletics
3. Wealthy UO alumni who give to OTHER universities or causes (indicating philanthropic capacity)
   but not UO Athletics — these are warm prospects being missed
4. UO alumni in tech (Silicon Valley, Seattle, Austin), finance, private equity, real estate,
   healthcare, and entertainment with significant accumulated wealth
5. Former UO student-athletes who went on to professional careers in sports or business with
   significant wealth — especially those NOT publicly connected to UO Athletics fundraising
6. UO alumni who serve on corporate boards, appear in proxy filings, or hold large equity stakes
7. Oregon-connected philanthropists who give to arts, education, or other causes but NOT UO Athletics
8. Search: "University of Oregon" alumni site:linkedin.com CEO OR founder, "UO grad" OR "Oregon Ducks"
   site:crunchbase.com, "University of Oregon alumni" Forbes, "graduated University of Oregon" acquisition

SPECIAL CATEGORY — UO Men's Basketball:
Also identify prospects with a specific connection or affinity for UO Men's Basketball who could
make a transformational gift specifically to the basketball program. Search for:
- Former UO Men's Basketball players with significant post-career wealth
- Oregon alumni who are known basketball fans or have given to other basketball programs
- Business leaders in basketball-heavy markets (Portland, LA, Bay Area, Chicago, NYC) with UO ties
- Prospects who played basketball at UO or had family members who did

For EACH prospect, conduct deep research and provide this exact JSON structure:

{
  "name": "Full Name",
  "uo_connection": "Specific UO connection - class year, degree, sport played, etc.",
  "current_role": "Current title and organization",
  "location": "City, State/Country",
  "estimated_net_worth": "Best estimate with range e.g. $75M-$150M",
  "giving_capacity": "Estimated max philanthropic gift capacity for UO Athletics",
  "capacity_rating": "TIER_1_TRANSFORMATIONAL (>$25M), TIER_2_PRINCIPAL ($10-25M), or TIER_3_MAJOR ($5-10M)",
  "basketball_prospect": true or false,
  "basketball_reason": "Why this person is a strong Men's Basketball prospect, or null if not applicable",
  "wealth_sources": "How they built their wealth - company, industry, events",
  "recent_news": "Most important recent news about them from the last 12 months",
  "existing_uo_giving": "Any known UO giving history — if none found, state 'No known UO Athletics giving identified'",
  "athletics_connection": "Any known connection to UO Athletics, sports giving, or stadium/facility gifts",
  "philanthropy_history": "Known charitable giving to OTHER institutions or causes — key signal of capacity",
  "why_prospect": "2-3 sentences on why this person is a strong UNDISCOVERED UO Athletics prospect",
  "engagement_angle": "Best approach or conversation opener for outreach — be specific",
  "urgency_flag": "Any time-sensitive wealth event or opportunity window",
  "contact_email": "Best publicly available or professionally discoverable email address, or null",
  "contact_phone": "Best publicly available phone number (office, cell if known), or null",
  "contact_address": "Best known business or home address from public records, or null",
  "contact_linkedin": "LinkedIn profile URL if found, or null",
  "contact_assistant": "Name and contact info for their executive assistant or office, if found",
  "sources": ["source1 title and URL", "source2 title and URL"],
  "last_updated": "YYYY-MM-DD",
  "confidence": "HIGH, MEDIUM, or LOW - confidence in the wealth/capacity estimate"
}

For EACH prospect, also search specifically for their contact information:
- Search "[name] email address" "[name] contact" "[name] office phone"
- Search their company website for executive contact pages
- Search LinkedIn for their profile URL
- Check SEC filings, corporate proxy statements for business addresses
- Search county property records for home address if publicly available

Find at least 10 distinct, deeply researched prospects. Quality over quantity.
Only include people with:
- Clear University of Oregon connection (alumni, former athlete, family connection)
- Estimated net worth of $25 million or more (capacity to give $5M+)
- NO known history of transformational giving to UO Athletics
- Verifiable information from news, public records, SEC filings, or credible sources

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

    # Rotate search focus each run to find different prospect pools
    search_angles = [
        "Focus especially on UO alumni in tech and venture capital — Silicon Valley, Seattle, Austin. Search AngelList, Crunchbase, TechCrunch for UO founders and executives.",
        "Focus especially on UO alumni in finance, private equity, hedge funds, and investment banking. Search for UO graduates at top financial firms.",
        "Focus especially on former UO athletes — football, track, basketball, baseball — who built wealth after their playing careers in business, media, or entertainment.",
        "Focus especially on UO alumni in real estate development, construction, and property investment across the Pacific Northwest and nationally.",
        "Focus especially on UO alumni who give to OTHER universities (Stanford, Oregon State, USC, etc.) or have established their own foundations — they have proven philanthropic capacity.",
        "Focus especially on UO alumni in healthcare, biotech, pharmaceuticals, and medical devices.",
        "Focus especially on UO alumni in media, entertainment, sports business, and gaming.",
        "Focus especially on UO alumni in retail, consumer brands, food and beverage.",
    ]
    angle = random.choice(search_angles)

    prompt = RESEARCH_PROMPT + f"\n\nTODAY'S SEARCH FOCUS: {angle}"
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
        if "basketball_prospect" not in p:
            p["basketball_prospect"] = False

    all_prospects, run_entry = merge_and_save(new_prospects, existing_prospects, run_history)

    basketball_count = sum(1 for p in all_prospects if p.get('basketball_prospect'))
    print(f"Run complete. {run_entry['added']} new, {run_entry['updated']} updated. Total: {run_entry['total_in_database']}")
    print(f"Tier 1 Transformational (>$25M capacity): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_1_TRANSFORMATIONAL')}")
    print(f"Tier 2 Principal ($10-25M): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_2_PRINCIPAL')}")
    print(f"Tier 3 Major ($5-10M): {sum(1 for p in all_prospects if p.get('capacity_rating') == 'TIER_3_MAJOR')}")
    print(f"Men's Basketball Prospects: {basketball_count}")


if __name__ == "__main__":
    run_agent()
