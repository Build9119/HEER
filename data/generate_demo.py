#!/usr/bin/env python3
"""Generate demo fixtures for HEER.

Fixed random seed -> the graph is identical every run.
Safe to screen-record: all names and numbers are invented.

Usage:  python3 data/generate_demo.py
Output: data/demo/  (markdown + text + pdf)
"""

import os

SEED = 42
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo")

# ---------------------------------------------------------------------------
# Invented fixtures shaped like Pankaj's real business.
# ---------------------------------------------------------------------------

CLIENTS = [
    {
        "name": "Meridian Bank Group",
        "industry": "Banking",
        "deal": "AI governance framework for 3 business lines",
        "value": 420000,
        "status": "Active",
        "contact": "Priya Raman, CISO",
        "notes": [
            "Kickoff done 2026-01-12. Steering committee monthly.",
            "Regulatory mapping: RBI, DPDP Act, EU AI Act exposure.",
            "Risk register v2 approved. Next: control testing.",
        ],
    },
    {
        "name": "Northwind Health",
        "industry": "Healthcare",
        "deal": "AI risk assessment + model inventory",
        "value": 185000,
        "status": "Active",
        "contact": "Dr. Alan Voss, Chief Digital Officer",
        "notes": [
            "Inventory: 14 models in production, 9 in pilot.",
            "Gap: no model registry. Recommend AI-GOS discovery module.",
            "Upsell path: governance operating layer, Q3.",
        ],
    },
    {
        "name": "Atlas Logistics",
        "industry": "Logistics",
        "deal": "Cybersecurity posture review + AI ops",
        "value": 96000,
        "status": "Proposal",
        "contact": "Meera Nair, COO",
        "notes": [
            "Proposal sent 2026-02-20. Follow-up due 2026-03-05.",
            "Competitor: two boutiques, no AI governance angle.",
            "Win probability: 0.6. Price anchor: 96k vs 120k list.",
        ],
    },
    {
        "name": "FinEdge Capital",
        "industry": "Fintech",
        "deal": "AI-GOS pilot — orchestration + observability",
        "value": 250000,
        "status": "Negotiation",
        "contact": "Sandeep Iyer, CTO",
        "notes": [
            "Pilot scoped: 2 use cases, 8 weeks.",
            "Sticking point: data residency. Need EU region answer.",
            "Decision expected 2026-03-10.",
        ],
    },
    {
        "name": "Verdant Retail",
        "industry": "Retail",
        "deal": "AI governance readiness assessment",
        "value": 45000,
        "status": "Closed",
        "contact": "Kavita Shah, Head of Digital",
        "notes": [
            "Delivered 2025-11-20. 14 findings, 3 critical.",
            "No follow-on yet. Re-engage Q2 with AI-GOS lite.",
        ],
    },
]

PROJECTS = [
    {
        "name": "AI-GOS",
        "type": "Product",
        "status": "In development",
        "description": "AI Governance Operating System.",
        "notes": [
            "Legacy: discover, govern, secure, orchestrate, optimize.",
            "Modules: Discovery, Governance, Security, Orchestration, Optimization.",
            "Target: enterprise CISOs and AI leads.",
            "Pricing: platform license + per-module. Not public yet.",
            "Competitors: Credo AI, Holistic AI, IBM watsonx.governance.",
            "Differentiator: operating layer, not just compliance reporting.",
        ],
        "links": [
            "AI-GOS positioning",
            "AI-GOS security module",
            "Pricing principles",
            "Client: Meridian Bank",
            "Personal",
        ],
    },
    {
        "name": "Radius Systems Pvt. Ltd.",
        "type": "Company",
        "description": "Technology and product development company.",
        "notes": [
            "Delivery arm for AI-GOS and client engagements.",
            "Team: 14 engineers, 2 PMs, 1 designer.",
            "Stack: Python, React, Kubernetes, AWS.",
        ],
        "links": ["Hiring", "AI-GOS"],
    },
    {
        "name": "Sip & Slice",
        "type": "Venture",
        "description": "Container café — coffee and wood-fired pizza.",
        "notes": [
            "Location: Pune. Container build, 2 units.",
            "Opened 2025-09-15. Break-even target: 2026-06.",
            "Avg daily covers: 120. Ticket: ₹420.",
            "Seasonal menu change due April.",
        ],
        "links": ["Sip & Slice expansion"],
    },
]

NOTES = [
    ("AI-GOS positioning", "Sell the operating layer, not a compliance checkbox. Buyers are CISOs and CDOs. The wedge is discovery — every enterprise has shadow AI.", ["AI-GOS"]),
    ("Pricing principles", "Never invent pricing. Engagement/product dependent. Anchor high, justify with scope. Discounts only for multi-year.", ["AI-GOS", "Client: Meridian Bank"]),
    ("Speaking", "Keynote: AI governance in practice, Pune Tech Week 2026-04-18. Draft slides by 2026-03-20.", ["AI-GOS"]),
    ("Hiring", "Need: senior AI engineer with governance experience. Budget 40-55L. Interview loop: 2 technical + 1 culture.", ["Radius Systems Pvt. Ltd."]),
    ("Sip & Slice expansion", "Second container site: Hinjewadi. Lease terms on table. Decision by 2026-04-01.", ["Sip & Slice"]),
    ("AI-GOS security module", "Design doc v0.3. Key: model inventory + runtime monitoring. Integrate with existing SIEM.", ["AI-GOS"]),
    ("Client: Meridian Bank", "Follow-up on AI-GOS pilot. They want a security-first narrative. Send case study from FinEdge.", ["AI-GOS", "Meridian Bank Group"]),
    ("Personal", "Focus: 3 big rocks per quarter. Q1: AI-GOS pilot, Atlas close, Sip & Slice break-even.", ["AI-GOS", "Sip & Slice", "Atlas Logistics"]),
]

# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_md(path, title, body, links=None):
    with open(path, "w") as f:
        f.write(f"# {title}\n\n")
        f.write(body.strip() + "\n")
        if links:
            f.write("\n\n## Links\n")
            for l in links:
                f.write(f"- [[{l}]]\n")


def write_pdf(path, body):
    # Minimal valid PDF (single page, plain text). Good enough for the demo.
    content = body.encode("latin-1", "replace")
    length = str(len(content)).encode("ascii")
    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
        b"4 0 obj<</Length " + length + b">>stream\n"
        + content
        + b"\nendstream endobj\n"
        b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF\n"
    )
    with open(path, "wb") as f:
        f.write(pdf)


def main():
    os.makedirs(OUT, exist_ok=True)

    # Clients
    clients_dir = os.path.join(OUT, "clients")
    os.makedirs(clients_dir, exist_ok=True)
    for c in CLIENTS:
        slug = c["name"].lower().replace(" ", "_")
        body = (
            f"Industry: {c['industry']}\n"
            f"Deal: {c['deal']}\n"
            f"Value: ${c['value']:,}\n"
            f"Status: {c['status']}\n"
            f"Contact: {c['contact']}\n\n"
            + "\n\n".join(f"- {n}" for n in c["notes"])
        )
        write_md(os.path.join(clients_dir, f"{slug}.md"), c["name"], body)

    # Projects
    projects_dir = os.path.join(OUT, "projects")
    os.makedirs(projects_dir, exist_ok=True)
    for p in PROJECTS:
        slug = p["name"].lower().replace(" ", "_").replace("&", "and")
        body = (
            f"Type: {p.get('type', 'Project')}\n"
            f"Status: {p.get('status', '')}\n\n"
            f"{p.get('description', 'No description.')}\n\n"
            + "\n\n".join(f"- {n}" for n in p["notes"])
        )
        write_md(
            os.path.join(projects_dir, f"{slug}.md"),
            p["name"],
            body,
            p.get("links"),
        )

    # Notes
    notes_dir = os.path.join(OUT, "notes")
    os.makedirs(notes_dir, exist_ok=True)
    for i, (title, body, links) in enumerate(NOTES):
        slug = title.lower().replace(" ", "_").replace(":", "").replace("&", "and")
        write_md(
            os.path.join(notes_dir, f"{i:02d}_{slug}.md"),
            title,
            body,
            links,
        )

    # A couple of PDFs to prove PDF indexing works
    pdf_dir = os.path.join(OUT, "reports")
    os.makedirs(pdf_dir, exist_ok=True)
    write_pdf(
        os.path.join(pdf_dir, "ai_gos_whitepaper.pdf"),
        "AI-GOS Whitepaper\n\n"
        "The AI Governance Operating System discovers, governs, secures, "
        "orchestrates and optimizes AI systems across the enterprise. "
        "This is the operating layer, not a compliance checkbox.",
    )
    write_pdf(
        os.path.join(pdf_dir, "market_scan.pdf"),
        "Market Scan 2026\n\n"
        "Competitors: Credo AI, Holistic AI, IBM watsonx.governance. "
        "Our wedge: the operating layer. CISOs buy outcomes, not reports.",
    )

    # Summary
    total = sum(len(files) for _, _, files in os.walk(OUT))
    print(f"Demo data generated: {OUT}")
    print(f"Files: {total}")
    print(f"Seed: {SEED}")


if __name__ == "__main__":
    main()