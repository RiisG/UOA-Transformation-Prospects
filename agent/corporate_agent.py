#!/usr/bin/env python3
"""
UO Athletics Corporate Sponsorship Prospect Agent
Finds companies led by UO alumni that would benefit from a transformational
corporate sponsorship deal with UO Athletics — NOT already Learfield partners.
"""

import anthropic
import json
import os
import random
import sys
from datetime import datetime, date
from pathlib import Path

PROSPECTS_FILE = Path(__file__).parent.parent / "docs" / "prospects.json"

SYSTEM_PROMPT = """You are the foremost expert in Division I collegiate athletics corporate sponsorships
and a world-class corporate prospect researcher. You have deep knowledge of:
- How Learfield, IMG College, and athletics multimedia rights partnerships work
- What companies gain from DI athletics sponsorships (brand awareness, B2B networking, recruiting,
  community goodwill, naming rights, digital/broadcast exposure, suite access, NIL tie-ins)
- How to identify the perfect match between a company's business goals and an athletics program's assets
- University of Oregon Athletics assets: Autzen Stadium (55,000 capacity), Matthew Knight Arena,
  Hayward Field (world's premier track facility), Nike/Jordan Brand identity, Pac-12/Big Ten exposure,
  national championship contender programs, elite recruiting pipeline
- Current UO Athletics Learfield corporate partners to AVOID (Nike, Pepsi, Subway, etc.)

You are thorough, strategic, and always cite sources."""

RESEARCH_PROMPT = """Your task is to identify companies led by University of Oregon alumni that:
1. Are large enough to make a TRANSFORMATIONAL corporate sponsorship deal ($500K–$5M+ annually)
2. Have NOT already made a corporate sponsorship deal with UO Athletics through Learfield or directly
3. Would BENEFIT significantly from a UO Athletics corporate partnership
4. Are led by a CEO, founder, or owner who is a UO alumni

IMPORTANT — DO NOT include companies already known as UO Athletics corporate sponsors such as:
Nike, Pepsi/PepsiCo, Subway, Banner Bank, Pacific Power, GEICO, Verizon, or other known Learfield
UO Athletics partners. Only surface NEW, undiscovered corporate prospects.

Use web search extensively. Search for:
1. University of Oregon alumni who are CEOs or founders of mid-to-large companies ($50M+ revenue)
2. Search "University of Oregon alumni CEO" site:linkedin.com OR site:businessjournals.com
3. Search Oregon Business Journal, Portland Business Journal, Eugene Business Journal for UO-led companies
4. Search Crunchbase, PitchBook for UO-founded companies that have scaled
5. Search for UO alumni in industries with strong athletics sponsorship ROI:
   - Financial services, wealth management, insurance (B2B networking, suite access)
   - Healthcare systems, medical devices, pharmaceuticals (community/brand)
   - Real estate, construction, development (naming rights, stadium signage)
   - Technology, software, cybersecurity (recruiting pipeline, brand)
   - Automotive dealerships, retail chains (local/regional brand)
   - Food & beverage, restaurants, hospitality (activation, fan engagement)
   - Legal, accounting, professional services (B2B, suite/hospitality)
   - Energy, utilities, cannabis/hemp, agriculture
6. Search specifically for companies in Oregon, Washington, California, Nevada led by UO alumni
7. Search for companies that sponsor other Pac-12/Big Ten schools but NOT Oregon
8. Search "University of Oregon" alumni Forbes, "UO graduate" company CEO founder

For EACH corporate prospect, research deeply and provide this exact JSON structure:

{
  "company_name": "Full legal company name",
  "company_type": "Industry sector (e.g. Financial Services, Healthcare, Tech, Real Estate)",
  "company_size": "Estimated annual revenue or employee count",
  "company_hq": "City, State",
  "company_website": "Website URL",
  "uo_alumni_leader": "Name of UO alumni CEO/founder/owner",
  "alumni_uo_connection": "Class year, degree, sport played, etc.",
  "alumni_current_title": "CEO / Founder / Owner / President etc.",
  "sponsorship_tier": "NAMING_RIGHTS ($5M+/yr), PRESENTING_SPONSOR ($1-5M/yr), PREMIER_PARTNER ($500K-1M/yr), or ASSOCIATE_PARTNER ($100-500K/yr)",
  "basketball_fit": true or false,
  "basketball_fit_reason": "Why this company is a strong UO Men's Basketball specific partner, or null",
  "sponsorship_value_to_company": "Specific, detailed business case — what does this company gain from UO Athletics sponsorship? Be specific about brand exposure, B2B networking, recruiting, naming rights, etc.",
  "recommended_deal_structure": "Specific sponsorship package recommendation — what assets, activations, rights",
  "existing_sports_sponsorships": "Any current sports sponsorships they have — signals appetite and capacity",
  "existing_uo_relationship": "Any current relationship with UO (not athletics) — foundation, academic, etc.",
  "why_now": "Why is this the right moment to approach this company?",
  "engagement_angle": "How to approach — who to call, what to say, what angle to use",
  "decision_maker_contact": "Best contact info for the decision maker (CEO/CMO/VP Marketing)",
  "company_phone": "Main company phone number",
  "company_address": "Full company headquarters address",
  "company_linkedin": "Company LinkedIn URL",
  "urgency_flag": "Any time-sensitive opportunity (fiscal year end, new funding, expansion announcement, etc.)",
  "sources": ["source1 title and URL", "source2 title and URL"],
  "last_updated": "YYYY-MM-DD",
  "confidence": "HIGH, MEDIUM, or LOW"
}

Find at least 10 strong corporate prospects. Quality and specificity are critical.
Only include companies where:
- The CEO/founder/owner has a clear UO connection
- The company has sufficient revenue/scale for a meaningful sponsorship
- There is a genuine, articulable business case for the partnership
- The company is NOT already a known UO Athletics/Learfield corporate partner

Return ONLY a valid JSON array. No introduction, no explanation, just the JSON array starting with [ and ending with ]."""

SEARCH_ANGLES = [
    "Focus on financial services, wealth management, banking, and insurance companies led by UO alumni.",
    "Focus on technology, software, SaaS, and cybersecurity companies led by UO alumni.",
    "Focus on real estate, construction, development, and property management companies led by UO alumni.",
    "Focus on healthcare, biotech, medical devices, and dental/veterinary companies led by UO alumni.",
    "Focus on retail, consumer brands, food & beverage, restaurants, and hospitality companies led by UO alumni.",
    "Focus on automotive dealerships, transportation, logistics, and energy companies led by UO alumni.",
    "Focus on media, entertainment, sports business, marketing agencies, and PR firms led by UO alumni.",
    "Focus on legal, accounting, consulting, and professional services firms led by UO alumni.",
]


def load_existing():
    if PROSPECTS_FILE.exists():
        with open(PROSPECTS_FILE) as f:
            data = json.load(f)
            return data.get("corporate_prospects", []), data
    return [], {}


def merge_and_save(new_corps, existing_corps, full_data):
    existing_by_name = {p["company_name"].lower().strip(): p for p in existing_corps}

    added = 0
    updated = 0
    for p in new_corps:
        key = p["company_name"].lower().strip()
        if key in existing_by_name:
            existing_by_name[key] = p
            updated += 1
        else:
            existing_by_name[key] = p
            added += 1

    all_corps = list(existing_by_name.values())

    tier_order = {"NAMING_RIGHTS": 0, "PRESENTING_SPONSOR": 1, "PREMIER_PARTNER": 2, "ASSOCIATE_PARTNER": 3}
    all_corps.sort(key=lambda p: tier_order.get(p.get("sponsorship_tier", "ASSOCIATE_PARTNER"), 4))

    full_data["corporate_prospects"] = all_corps
    full_data["corporate_total"] = len(all_corps)
    full_data["corporate_basketball_count"] = sum(1 for p in all_corps if p.get("basketball_fit"))
    full_data["corporate_last_updated"] = datetime.now().isoformat()

    PROSPECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROSPECTS_FILE, "w") as f:
        json.dump(full_data, f, indent=2)

    print(f"Corporate database updated: {len(all_corps)} total ({added} new, {updated} refreshed)")
    return all_corps


def run_corporate_agent():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] UO Athletics Corporate Sponsorship Research starting...")

    existing_corps, full_data = load_existing()
    existing_names = [p["company_name"] for p in existing_corps]

    angle = random.choice(SEARCH_ANGLES)
    prompt = RESEARCH_PROMPT + f"\n\nTODAY'S SEARCH FOCUS: {angle}"
    if existing_names:
        avoid = ", ".join(existing_names[:30])
        prompt += f"\n\nNOTE: These companies are already in the database — find NEW ones not on this list: {avoid}"

    print(f"Search angle: {angle[:60]}...")
    print("Conducting deep corporate sponsorship research (3-5 minutes)...")

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

    result_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result_text = block.text

    if not result_text:
        print("ERROR: No text response")
        sys.exit(1)

    try:
        start = result_text.find("[")
        if start < 0:
            print("ERROR: No JSON array found")
            print("Response:", result_text[:500])
            sys.exit(1)
        depth = 0
        end = start
        for i, ch in enumerate(result_text[start:], start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        new_corps = json.loads(result_text[start:end])
        print(f"Agent found {len(new_corps)} corporate prospects")
    except json.JSONDecodeError as e:
        print(f"ERROR parsing JSON: {e}")
        print("Response (first 1000):", result_text[:1000])
        sys.exit(1)

    today = str(date.today())
    for p in new_corps:
        if "last_updated" not in p or not p["last_updated"]:
            p["last_updated"] = today
        tier = p.get("sponsorship_tier", "")
        if "NAMING" in tier:
            p["sponsorship_tier"] = "NAMING_RIGHTS"
        elif "PRESENTING" in tier:
            p["sponsorship_tier"] = "PRESENTING_SPONSOR"
        elif "PREMIER" in tier:
            p["sponsorship_tier"] = "PREMIER_PARTNER"
        else:
            p["sponsorship_tier"] = "ASSOCIATE_PARTNER"
        if "basketball_fit" not in p:
            p["basketball_fit"] = False

    all_corps = merge_and_save(new_corps, existing_corps, full_data)

    bball = sum(1 for p in all_corps if p.get("basketball_fit"))
    naming = sum(1 for p in all_corps if p.get("sponsorship_tier") == "NAMING_RIGHTS")
    presenting = sum(1 for p in all_corps if p.get("sponsorship_tier") == "PRESENTING_SPONSOR")
    premier = sum(1 for p in all_corps if p.get("sponsorship_tier") == "PREMIER_PARTNER")
    print(f"Naming Rights ($5M+): {naming} | Presenting ($1-5M): {presenting} | Premier ($500K-1M): {premier}")
    print(f"Men's Basketball fits: {bball}")


if __name__ == "__main__":
    run_corporate_agent()
