# Legal Review Queue — PortSwigger AI Pioneer Application

*Jonathon Graham · June 2026*

---

## Open these first

**`demo.html`** — opens in any browser, no setup. A working UI showing contracts arriving pre-sorted by urgency, with AI analysis done before the lawyer opens their laptop.

**`vision-diagram.html`** — the system architecture: full flow from email inbox to review queue, and the thinking behind why it's built this way.

The rest of the folder is the working code. If you want to run it locally, it takes a couple of minutes (see `Setup` at the bottom). You'll need an Anthropic API key.

---

## What I actually built, and why

You asked how AI could help the legal team with contract review. Most answers to that question stop at "summarise the contract and highlight unusual clauses." That's the wrong frame.

The team's bottleneck isn't reading speed. Every contract sits in the same pile looking equally important until someone opens it. The real question is whether AI can tell a lawyer what they need to read before they open the document, not help them get through it faster once they do.

So I built a triage queue.

Contracts arrive. The AI reads them first. By the time the lawyer opens the queue, each contract already has a status (urgent, review required, or no action) with the reasoning behind it. They work top to bottom, urgent first, and skip the boilerplate entirely when the AI has already confirmed it's clean.

---

## The part that actually matters: the playbook

Most AI contract tools work by asking the model to "identify unusual clauses." That's not a useful instruction. A general-purpose AI inventing legal positions is a liability.

The way I've built this, the AI has one job: compare what's in this contract against what PortSwigger's legal team has already agreed is acceptable. Every finding cites the established position it's based on. Every suggested redline comes from prior decisions, not the model's imagination.

The playbook (`data/playbook.json`) holds 16 standard positions across NDAs and order forms. The AI retrieves the relevant ones, applies them to the contract, and flags where the contract deviates and by how much.

The system also improves the way your legal team does: by accumulating decisions. Every override, every new clause type, every novel issue your lawyers resolve goes back into the playbook. No retraining needed. The more it's used, the less it escalates.

---

## The trust ladder

Nobody should trust the AI on day one. This is built for a slow build:

| Phase | What the lawyer does | What the AI does |
|---|---|---|
| Now | Reads everything, but arrives briefed | Pre-analysis, flags what needs attention |
| 3 months | Reads flagged clauses only | Approves standard clauses autonomously |
| 6 months | Spot-checks a sample of approvals | Handles triage almost entirely |

Phase 1 success looks like this: the lawyer spent 5 minutes instead of 30, and the AI didn't miss anything the lawyer would have caught.

---

## The piece nobody mentions

Your brief touched on the end-of-month backlog without naming the actual cause. Sales doesn't know which of their deals are in the legal queue. Legal doesn't know which deals are time-sensitive to sales. Both teams are working from separate inboxes with no shared view, so legal triages by arrival order and sales just waits.

A shared pipeline fixes both at once. Sales sees which of their contracts have been pre-reviewed and what the AI flagged. Legal sees which ones sales are actively chasing. The end-of-month blindspot becomes visible before it becomes a problem, not after.

That's what I'd build next.

---

## What's in the demo

Two urgent contracts (GlobalTech Ventures NDA, Meridian Financial Order Form), one review-required (Synapse Cloud NDA), and one clean boilerplate NDA (Acme Technology).

Click into either of the urgent ones: the AI has already written the redline. The lawyer reads one clause and decides whether they agree.

---

## Setup (if you want to run the full app)

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
cp .env.example .env
# Edit .env → ANTHROPIC_API_KEY=your_key_here

# Run
streamlit run app.py
# Opens at http://localhost:8501
```

Drop any PDF, DOCX, or TXT contract into the app and it'll analyse it live against the playbook.

---

## Project structure

```
contract-reviewer/
├── demo.html             ← Start here
├── vision-diagram.html   ← System architecture
├── app.py                ← Streamlit UI (the working app)
├── reviewer.py           ← AI analysis engine
├── knowledge_base.py     ← ChromaDB vector store (playbook retrieval)
├── ingest.py             ← PDF / DOCX / TXT extraction
├── data/
│   ├── playbook.json     ← The source of truth (16 established positions)
│   └── samples/          ← Drop test contracts here for Scan Inbox
└── requirements.txt
```

---

*Stack: Python · Streamlit · ChromaDB · Anthropic Claude API*
