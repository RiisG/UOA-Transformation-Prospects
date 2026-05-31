#!/usr/bin/env python3
"""
Contact enrichment pass — searches for phone, email, address, LinkedIn for each prospect.
"""
import anthropic
import json
import os
import sys
import time
from pathlib import Path

PROSPECTS_FILE = Path(__file__).parent.parent / "docs" / "prospects.json"


def enrich_contact(client, prospect):
    name = prospect["name"]
    role = prospect.get("current_role", "")
    location = prospect.get("location", "")

    prompt = f"""You are a professional prospect researcher. Find publicly available contact information for:

Name: {name}
Role: {role}
Location: {location}

Search extensively for:
1. Business email address (try company website staff pages, press releases, SEC filings, news articles)
2. Office or cell phone number (company website, press releases, public filings)
3. Business or home mailing address (company headquarters, property records, SEC filings)
4. LinkedIn profile URL (search LinkedIn directly)
5. Executive assistant name and contact info (company website, press releases)

Search queries to use:
- "{name}" email contact
- "{name}" phone number
- "{name}" address "{location}"
- "{name}" LinkedIn
- "{name}" executive assistant
- site:linkedin.com "{name}"
- "{name}" "{role}" contact

Return ONLY a JSON object with these exact keys (use null if not found):
{{
  "contact_email": "email address or null",
  "contact_phone": "phone number or null",
  "contact_address": "full mailing address or null",
  "contact_linkedin": "full LinkedIn URL or null",
  "contact_assistant": "assistant name and contact or null"
}}

Only include information you actually found from web searches. Do not guess or fabricate.
Return ONLY the JSON object, nothing else."""

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1000,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 8
        }],
        messages=[{"role": "user", "content": prompt}]
    )

    result_text = ""
    for block in response.content:
        if hasattr(block, "type") and block.type == "text":
            result_text = block.text

    try:
        start = result_text.find("{")
        end = result_text.rfind("}") + 1
        if start >= 0 and end > start:
            contact = json.loads(result_text[start:end])
            return contact
    except Exception:
        pass
    return {}


def run_enrichment():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    with open(PROSPECTS_FILE) as f:
        data = json.load(f)

    prospects = data["prospects"]
    total = len(prospects)
    enriched = 0

    for i, prospect in enumerate(prospects):
        name = prospect["name"]
        # Skip if already has contact info
        if any(prospect.get(f) for f in ["contact_email", "contact_phone", "contact_address", "contact_linkedin"]):
            print(f"[{i+1}/{total}] {name} — already has contact info, skipping")
            continue

        print(f"[{i+1}/{total}] Searching contacts for: {name}...")
        try:
            contact = enrich_contact(client, prospect)
            found = [k for k, v in contact.items() if v and v != "null"]
            if found:
                prospect.update(contact)
                enriched += 1
                print(f"  Found: {', '.join(found)}")
            else:
                print(f"  No contact info found")
            # Brief pause between requests
            time.sleep(1)
        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    with open(PROSPECTS_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nEnrichment complete. {enriched} prospects updated with contact info.")


if __name__ == "__main__":
    run_enrichment()
