"""
reviewer.py — Core AI contract analysis.

The AI does not invent legal positions.
It applies PortSwigger's established positions, retrieved from the playbook.
Every finding cites the precedent it is based on.
"""

import json
import os
from typing import Dict, List

from dotenv import load_dotenv

load_dotenv()


def _build_system_prompt(precedents: List[Dict]) -> str:
    positions_text = ""
    for p in precedents:
        m = p["metadata"]
        redline = m.get("suggested_redline", "")
        positions_text += (
            f"\n---\n"
            f"ISSUE: {m['issue']}\n"
            f"STANDARD POSITION: {m['standard_position']}\n"
            f"SUGGESTED REDLINE: {redline if redline else 'None required — clause is acceptable as-is'}\n"
            f"DEFAULT ACTION: {m['action'].upper()}\n"
            f"PRECEDENTS: {m['precedent_count']} prior instances\n"
        )

    return f"""You are a contract review AI assistant for PortSwigger Ltd, a UK cybersecurity software company.

Your job is to pre-review commercial contracts — typically mutual NDAs and customer order forms — against PortSwigger's established legal positions. You act as a junior associate: you read the contract, identify what needs attention, and brief the senior lawyer on exactly where to focus.

PortSwigger's established positions on common issues:
{positions_text}

RULES YOU MUST FOLLOW:
1. Only flag issues that are actually present in the contract text — do not invent problems.
2. Only suggest redlines based on the established positions above — never invent a legal position.
3. If a clause matches PortSwigger's standard position, mark it as APPROVED — do not flag it.
4. If you encounter an issue with no matching precedent, mark it as NOVEL and escalate.
5. Every finding must cite which established position it is applying.
6. Be specific: tell the lawyer exactly which clause number or section to look at.
7. Plain English throughout — the goal is to save a lawyer time, not to impress them.

Respond ONLY with valid JSON. No prose, no markdown, no explanation outside the JSON structure."""


def analyse_contract(contract_text: str, precedents: List[Dict]) -> Dict:
    import anthropic

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Truncate to avoid token limits while keeping the most relevant content
    truncated_text = contract_text[:8000]

    user_prompt = f"""Analyse the following contract and return a structured JSON review.

CONTRACT TEXT:
{truncated_text}

Return JSON in exactly this structure — no other text:
{{
  "contract_type": "mutual_nda | customer_order_form | other",
  "overall_status": "no_action | review_required | urgent",
  "confidence": <integer 0-100>,
  "summary": "<2-3 sentence plain English summary of what this contract is and your overall assessment>",
  "reading_focus": "<Tell the lawyer exactly which clauses or sections to actually read. Be specific.>",
  "issues": [
    {{
      "clause_ref": "<Clause number or section name from the contract>",
      "issue_type": "<governing_law | confidentiality_term | liability_cap | ip_ownership | payment_terms | data_protection | non_solicitation | indemnification | assignment | termination | other>",
      "status": "<approved | review | urgent | novel>",
      "finding": "<What you found, in plain English>",
      "precedent_applied": "<Which established position this maps to, or null if novel>",
      "precedent_count": <integer or null>,
      "suggested_action": "<Exactly what the lawyer should do>",
      "suggested_redline": "<Exact replacement language if applicable, otherwise null>"
    }}
  ],
  "approved_count": <integer>,
  "flagged_count": <integer>,
  "novel_count": <integer>
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=_build_system_prompt(precedents),
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    # First attempt: parse as-is
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return _repair_and_parse(raw)


def _repair_and_parse(raw: str) -> Dict:
    """
    Attempt to recover truncated JSON by closing any open structures.
    Handles the common case where max_tokens cuts the response mid-string.
    """
    # Truncate at the last complete issue object we can find
    # Find the last fully closed } before the truncation point
    depth = 0
    last_safe = 0
    in_string = False
    escape_next = False

    for i, ch in enumerate(raw):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 1:
                # We just closed an issue object — safe recovery point
                last_safe = i + 1

    if last_safe == 0:
        raise ValueError("Could not recover any valid JSON from the response.")

    # Build a minimal valid document from what we have
    truncated = raw[:last_safe]

    # Close the issues array and top-level object
    repaired = truncated.rstrip().rstrip(",") + "\n  ],\n"
    repaired += '  "approved_count": 0,\n'
    repaired += '  "flagged_count": 0,\n'
    repaired += '  "novel_count": 0,\n'
    repaired += '  "_truncated": true\n'
    repaired += "}"

    result = json.loads(repaired)

    # Recount from recovered issues
    issues = result.get("issues", [])
    result["approved_count"] = sum(1 for i in issues if i.get("status") == "approved")
    result["flagged_count"]  = sum(1 for i in issues if i.get("status") in ("review", "urgent"))
    result["novel_count"]    = sum(1 for i in issues if i.get("status") == "novel")
    if not result.get("summary"):
        result["summary"] = "Analysis was partially truncated. Issues shown are complete; review counts may be incomplete."

    return result


def review_contract(contract_text: str, kb_collection) -> Dict:
    """Entry point: retrieves relevant precedents then runs AI analysis."""
    from knowledge_base import search_precedents

    precedents = search_precedents(kb_collection, contract_text, n_results=10)
    return analyse_contract(contract_text, precedents)
