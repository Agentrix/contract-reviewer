# Legal Review Queue — PortSwigger AI Pioneer Application

*Jonathon Graham · June 2026*

---

## Open these first

**`demo.html`** — opens in any browser, no setup. A working UI showing contracts arriving, pre-sorted by urgency, with AI analysis already done before the lawyer opens their laptop.

**`vision-diagram.html`** — the system architecture: full flow from email inbox to review queue, and the thinking behind why it's built this way.

The rest of the folder is the working code. If you want to run it locally, it takes a couple of minutes (`Setup` section at the bottom). You'll need an Anthropic API key.

---

## What I actually built, and why

You asked how AI could help the legal team with contract review. Most answers to that question stop at "summarise the contract and highlight unusual clauses." I didn't think that was the right framing.

The team's bottleneck isn't reading speed. It's the fact that every contract sits in the same pile looking equally important until someone opens it. The question isn't *can AI help me read this?* It's *can AI tell me what I need to read — and what I can safely skip?*

So I built a triage queue.

Contracts arrive. The AI reads them before anyone else does. By the time the lawyer opens the queue, each contract already has a status — urgent, review required, or no action — with the reasoning behind it. They work top to bottom. Urgent first. Standard boilerplate last, or not at all.

---

## The part that actually matters: the playbook

Most AI contract tools work by asking the model to "identify unusual clauses." That's not the right instruction. A general-purpose AI inventing legal positions is a liability, not a feature.

The way I've built this, the AI doesn't have opinions. It has one job: compare what's in this contract against what PortSwigger's legal team has already agreed is acceptable. Every finding cites the established position it's based on. Every suggested redline comes from prior decisions, not the model's imagination.

The playbook (`data/playbook.json`) is a structured knowledge base of 16 standard positions across NDAs and order forms. That's the source of truth. The AI retrieves the relevant entries, applies them to the contract in front of it, and flags where the contract deviates — and by how much.

That also means the system improves exactly the way your legal team does: by accumulating decisions. Every override, every new clause type, every novel issue your lawyers resolve — that goes back into the playbook. No retraining required. The more it's used, the less it needs to escalate.

---

## The trust ladder

This isn't asking anyone to trust the AI on day one. It's designed for a slow build:

| Phase | What the lawyer does | What the AI does |
|---|---|---|
| Now | Reads everything — but arrives briefed | Pre-analysis, flags what needs attention |
| 3 months | Reads flagged clauses only | Approves standard clauses autonomously |
| 6 months | Spot-checks a sample of approvals | Handles triage almost entirely |

The measure of success in Phase 1 isn't "the AI approved contracts." It's "the lawyer spent 5 minutes instead of 30, and wasn't wrong."

---

## The piece nobody mentions

There's a second problem your brief hinted at but didn't name directly. The end-of-month rush.

That's not purely a legal team problem. Sales doesn't know which of their deals are sitting in the legal queue. Legal doesn't know which deals are time-sensitive to sales. They're operating from separate inboxes with no shared view — so legal triages by arrival date, and sales just waits.

A shared pipeline view changes that. Sales sees which of their contracts have been pre-reviewed and what the AI flagged. Legal sees which ones the sales team are actively chasing. One system resolves both queues, and the end-of-month blindspot becomes visible before it becomes a problem.

That's what I'd want to build next.

---

## What's in the demo

The interactive demo has two urgent contracts (GlobalTech Ventures NDA, Meridian Financial Order Form), one review-required contract (Synapse Cloud NDA), and one clean boilerplate NDA (Acme Technology).

Click into any of the urgent ones to see what I mean: the AI has already written the redline. The lawyer's job is to read one clause and decide whether they agree.

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
