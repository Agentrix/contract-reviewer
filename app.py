"""
app.py — Contract Review AI · Legal Triage Queue
Run: streamlit run app.py
"""

import os
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from ingest import extract_text, extract_from_bytes
from knowledge_base import build_knowledge_base
from reviewer import review_contract

# ── Config ─────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Legal Review Queue",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SAMPLES_DIR = Path(__file__).parent / "data" / "samples"

STATUS_COLOUR = {
    "urgent":          "#ef4444",
    "review_required": "#f59e0b",
    "no_action":       "#22c55e",
}
STATUS_LABEL = {
    "urgent":          "🔴  Urgent",
    "review_required": "⚠️  Review Required",
    "no_action":       "✅  No Action",
}
STATUS_SORT  = {"urgent": 0, "review_required": 1, "no_action": 2}
ISSUE_ICON   = {"urgent": "🔴", "novel": "🔵", "review": "⚠️", "approved": "✅"}
ISSUE_SORT   = {"urgent": 0, "novel": 1, "review": 2, "approved": 3}
CONTRACT_TYPE = {
    "mutual_nda":          "Mutual NDA",
    "customer_order_form": "Customer Order Form",
    "other":               "Other",
}

# ── Styles ─────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
.block-container { padding-top: 1.2rem; max-width: 1100px; }

.summary-bar {
    display: flex;
    gap: 2rem;
    padding: 1.2rem 0 1rem 0;
    border-bottom: 1px solid #1e293b;
    margin-bottom: 1rem;
}
.stat-block .num { font-size: 2.2rem; font-weight: 800; line-height: 1; }
.stat-block .lbl { font-size: 0.72rem; color: #64748b; margin-top: 3px; letter-spacing: 0.04em; text-transform: uppercase; }

.contract-card {
    border-left: 5px solid var(--c, #888);
    background: #0f172a;
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem 0.85rem 1.25rem;
    margin-bottom: 0.6rem;
}
.c-title { font-size: 1rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.35rem 0; }
.c-meta  { font-size: 0.75rem; color: #64748b; margin: 0 0 0.45rem 0; }
.c-flag  { font-size: 0.83rem; color: #cbd5e1; margin: 0 0 0.35rem 0; }
.c-counts{ font-size: 0.75rem; margin: 0; }

.pill {
    display: inline-block;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    margin-right: 5px;
}
</style>
""", unsafe_allow_html=True)

# ── Knowledge base (cached) ────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading knowledge base…")
def get_kb():
    return build_knowledge_base()

# ── Helpers ────────────────────────────────────────────────────────────────────

def top_flag(result: dict) -> str:
    issues = sorted(result.get("issues", []), key=lambda x: ISSUE_SORT.get(x.get("status", "review"), 2))
    if not issues:
        return "No issues flagged"
    top = issues[0]
    icon = ISSUE_ICON.get(top.get("status", "review"), "⚠️")
    finding = top.get("finding", "")[:80]
    return f"{icon} {top.get('clause_ref', '')} — {finding}"


def run_analysis(text: str, filename: str, kb) -> dict:
    result = review_contract(text, kb)
    return {
        "filename": filename,
        "received": datetime.now().strftime("%d %b, %H:%M"),
        "result":   result,
    }


def sorted_queue(queue: list) -> list:
    return sorted(queue, key=lambda x: STATUS_SORT.get(
        x["result"].get("overall_status", "review_required"), 1
    ))

# ── Summary bar ────────────────────────────────────────────────────────────────

def render_summary_bar(queue: list):
    urgent  = sum(1 for c in queue if c["result"].get("overall_status") == "urgent")
    review  = sum(1 for c in queue if c["result"].get("overall_status") == "review_required")
    clear   = sum(1 for c in queue if c["result"].get("overall_status") == "no_action")

    st.markdown(f"""
    <div class="summary-bar">
        <div class="stat-block">
            <div class="num" style="color:#ef4444">{urgent}</div>
            <div class="lbl">Urgent</div>
        </div>
        <div class="stat-block">
            <div class="num" style="color:#f59e0b">{review}</div>
            <div class="lbl">Review Required</div>
        </div>
        <div class="stat-block">
            <div class="num" style="color:#22c55e">{clear}</div>
            <div class="lbl">No Action</div>
        </div>
        <div class="stat-block">
            <div class="num" style="color:#475569">{len(queue)}</div>
            <div class="lbl">Total</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── Queue view ─────────────────────────────────────────────────────────────────

def render_queue(queue: list):
    if not queue:
        st.markdown("""
        <div style="text-align:center; padding:4rem 0; color:#334155;">
            <div style="font-size:3rem">📭</div>
            <div style="font-size:1rem; margin-top:0.5rem; color:#475569">Queue is empty</div>
            <div style="font-size:0.82rem; margin-top:0.25rem; color:#334155">
                Click <strong>Scan Inbox</strong> or upload a contract to begin
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    for idx, item in enumerate(sorted_queue(queue)):
        r       = item["result"]
        status  = r.get("overall_status", "review_required")
        colour  = STATUS_COLOUR.get(status, "#888")
        slabel  = STATUS_LABEL.get(status, status)
        ctype   = CONTRACT_TYPE.get(r.get("contract_type", "other"), "Other")
        flag    = top_flag(r)
        flagged = r.get("flagged_count", 0)
        novel   = r.get("novel_count", 0)
        approved = r.get("approved_count", 0)

        counts_html = ""
        parts = []
        if flagged: parts.append(f'<span style="color:#ef4444">{flagged} flagged</span>')
        if novel:   parts.append(f'<span style="color:#a855f7">{novel} novel</span>')
        if approved: parts.append(f'<span style="color:#22c55e">{approved} approved</span>')
        counts_html = " &nbsp;·&nbsp; ".join(parts)

        card_col, btn_col = st.columns([6, 1])

        with card_col:
            st.markdown(f"""
            <div class="contract-card" style="--c:{colour}">
                <p class="c-title">{item['filename']}</p>
                <p class="c-meta">
                    <span class="pill" style="background:{colour}22;color:{colour}">{slabel}</span>
                    <span class="pill" style="background:#1e293b;color:#64748b">{ctype}</span>
                    Received {item['received']}
                </p>
                <p class="c-flag">{flag}</p>
                <p class="c-counts">{counts_html}</p>
            </div>
            """, unsafe_allow_html=True)

        with btn_col:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            if st.button("Open →", key=f"open_{idx}", use_container_width=True):
                st.session_state.selected = idx
                st.rerun()

# ── Detail view ────────────────────────────────────────────────────────────────

def render_detail(item: dict):
    r      = item["result"]
    status = r.get("overall_status", "review_required")
    colour = STATUS_COLOUR.get(status, "#888")
    slabel = STATUS_LABEL.get(status, status)
    ctype  = CONTRACT_TYPE.get(r.get("contract_type", "other"), "Other")

    if st.button("← Back to Queue"):
        del st.session_state.selected
        st.rerun()

    st.divider()

    # Contract header
    h1, h2, h3, h4 = st.columns([4, 1, 1, 1])
    h1.markdown(f"### {item['filename']}")
    h2.metric("Status", slabel)
    h3.metric("Type", ctype)
    h4.metric("AI Confidence", f"{r.get('confidence', 0)}%")

    st.divider()

    # Summary + reading focus
    st.markdown("**Summary**")
    st.info(r.get("summary", "—"))

    focus = r.get("reading_focus")
    if focus:
        st.markdown(
            f"<div style='background:#0f172a;border-left:3px solid #3b82f6;"
            f"padding:0.6rem 1rem;border-radius:0 6px 6px 0;font-size:0.85rem;"
            f"color:#93c5fd;margin:0.5rem 0'>"
            f"📌 <strong>Where to focus:</strong> {focus}</div>",
            unsafe_allow_html=True,
        )

    st.divider()

    # Issue counts summary
    flagged  = r.get("flagged_count", 0)
    novel    = r.get("novel_count", 0)
    approved = r.get("approved_count", 0)

    mc1, mc2, mc3 = st.columns(3)
    mc1.metric("Flagged",  flagged)
    mc2.metric("Novel",    novel)
    mc3.metric("Approved", approved)

    st.markdown("**Clause Analysis**")

    issues = sorted(r.get("issues", []), key=lambda x: ISSUE_SORT.get(x.get("status", "review"), 2))

    if not issues:
        st.success("No issues found — contract appears standard.")
    else:
        for issue in issues:
            s       = issue.get("status", "review")
            icon    = ISSUE_ICON.get(s, "⚠️")
            ref     = issue.get("clause_ref", "Unknown clause")
            finding = issue.get("finding", "")
            label   = f"{icon} **{ref}** — {finding[:90]}{'…' if len(finding) > 90 else ''}"

            with st.expander(label, expanded=(s in ("urgent", "novel"))):
                left, right = st.columns(2)
                with left:
                    st.markdown(f"**Finding:** {finding}")
                    p = issue.get("precedent_applied")
                    c = issue.get("precedent_count")
                    if p:
                        st.markdown(f"**Precedent:** {p}{f' ({c} prior instances)' if c else ''}")
                    else:
                        st.markdown("**Precedent:** None found — novel issue, escalate to senior review")
                with right:
                    if issue.get("suggested_action"):
                        st.markdown(f"**Action:** {issue['suggested_action']}")
                    if issue.get("suggested_redline"):
                        st.markdown("**Suggested redline:**")
                        st.code(issue["suggested_redline"], language=None)

    with st.expander("Raw JSON"):
        st.json(r)

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    kb = get_kb()

    if "queue" not in st.session_state:
        st.session_state.queue = []

    # ── Detail view ────────────────────────────────────────────────────────────
    if "selected" in st.session_state:
        q   = sorted_queue(st.session_state.queue)
        idx = st.session_state.selected
        if 0 <= idx < len(q):
            render_detail(q[idx])
        else:
            del st.session_state.selected
            st.rerun()
        return

    # ── Queue view ─────────────────────────────────────────────────────────────
    title_col, actions_col = st.columns([3, 2])

    with title_col:
        st.title("⚖️ Legal Review Queue")
        st.caption("Contracts are pre-reviewed on arrival. Work top to bottom — urgent first.")

    with actions_col:
        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        btn_col, upload_col = st.columns(2)

        with btn_col:
            if st.button("📥 Scan Inbox", type="primary", use_container_width=True):
                files = sorted([
                    f for f in SAMPLES_DIR.iterdir()
                    if f.suffix.lower() in (".pdf", ".docx", ".txt")
                    and not f.name.startswith(".")
                    and "PLACE_CONTRACTS" not in f.name
                ])
                existing = {c["filename"] for c in st.session_state.queue}
                new_files = [f for f in files if f.name not in existing]

                if not new_files:
                    st.toast("No new contracts found in inbox.", icon="📭")
                else:
                    progress = st.progress(0, text=f"Processing 0 / {len(new_files)}…")
                    for i, f in enumerate(new_files):
                        progress.progress((i) / len(new_files), text=f"Reviewing {f.name}…")
                        text = extract_text(str(f))
                        item = run_analysis(text, f.name, kb)
                        st.session_state.queue.append(item)
                    progress.progress(1.0, text="Done.")
                    st.rerun()

        with upload_col:
            uploaded = st.file_uploader(
                "upload",
                type=["pdf", "docx", "txt"],
                label_visibility="collapsed",
                key="uploader",
            )
            if uploaded:
                existing = {c["filename"] for c in st.session_state.queue}
                if uploaded.name not in existing:
                    with st.spinner(f"Reviewing {uploaded.name}…"):
                        text = extract_from_bytes(uploaded.read(), uploaded.name)
                        item = run_analysis(text, uploaded.name, kb)
                        st.session_state.queue.append(item)
                    st.rerun()

    # Summary bar + queue list
    if st.session_state.queue:
        render_summary_bar(st.session_state.queue)

    render_queue(st.session_state.queue)

    if st.session_state.queue:
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        if st.button("Clear queue", type="secondary"):
            st.session_state.queue = []
            st.rerun()


if __name__ == "__main__":
    main()
