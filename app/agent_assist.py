"""Agent assist screen: each ticket with its AI triage, a draft reply the agent can edit, and the reply's sources.

Run it from the project folder:
    streamlit run app/agent_assist.py

It only reads and saves data (Google Sheet or local files, depending on DATA_SOURCE). It never calls the AI,
so using it costs nothing.
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so "src" can be imported when run by Streamlit

import streamlit as st

from src.assist import NEEDS_PERSON, READY, build_views, filter_views, summary
from src.connectors import get_data_source
from src.models import ALL_RESULT_COLUMNS

# Background and text color for each label.
URGENCY = {"urgent": ("#fde2e1", "#a4161a"), "high": ("#ffedd5", "#9a4a00"),
           "medium": ("#dbeafe", "#1e4fa8"), "low": ("#dcfce7", "#16653a")}
SENTIMENT = {"positive": ("#dcfce7", "#16653a"), "neutral": ("#eceef2", "#454b57"),
             "frustrated": ("#ffe4d6", "#a5420f"), "angry": ("#fde2e1", "#a4161a")}
CHURN = {"low": ("#dcfce7", "#16653a"), "medium": ("#ffedd5", "#9a4a00"), "high": ("#fde2e1", "#a4161a")}
QUEUE = {"Priority Escalations": ("#fde2e1", "#a4161a"), "Billing": ("#e0e7ff", "#3730a3"),
         "Payments": ("#ccfbf1", "#0f6157"), "Technical": ("#dbeafe", "#1e4fa8"),
         "Store Setup": ("#f3e8ff", "#6b21a8"), "Account Security": ("#fce7f3", "#9d174d")}
CATEGORY = ("#ccfbf1", "#0f6157")
GRAY = ("#eceef2", "#454b57")
DOT = {"urgent": "red", "high": "orange", "medium": "blue", "low": "green"}

CSS = """
<style>
.block-container {padding-top: 2.6rem;}
.sa-header {background: #1e4fa8; color: #fff; border-radius: 8px; padding: 14px 18px; margin-bottom: 12px;}
.sa-header b {font-size: 1.3rem;}
.sa-header span {opacity: .85; margin-left: 10px;}
.sa-stats {display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 14px;}
.sa-stat {flex: 1 1 140px; border-radius: 8px; padding: 10px 14px;}
.sa-stat .n {font-size: 1.6rem; font-weight: 700; line-height: 1.1;}
.sa-stat .l {font-size: .85rem;}
.sa-card {border: 1px solid #dde1e8; border-radius: 8px; padding: 14px 16px; margin-bottom: 12px; background: #fff; color: #1d2430;}
.sa-card h3 {margin: 0 0 4px 0; font-size: 1.25rem;}
.sa-meta {color: #5b6575; font-size: .9rem; margin-bottom: 8px;}
.sa-body {white-space: pre-wrap;}
.sa-badges {display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px;}
.sa-badge {border-radius: 999px; padding: 2px 10px; font-size: .85rem; font-weight: 600;}
.sa-label {font-size: .75rem; text-transform: uppercase; letter-spacing: .05em; color: #5b6575; font-weight: 600;}
.st-key-save button {background: #16a34a; border-color: #16a34a; color: #fff;}
.st-key-save button:hover {background: #15803d; border-color: #15803d; color: #fff;}
.st-key-person button {background: #f59e0b; border-color: #f59e0b; color: #1d2430;}
.st-key-person button:hover {background: #d97706; border-color: #d97706; color: #1d2430;}
</style>
"""


def badge(text: str, colors: tuple[str, str], prefix: str = "") -> str:
    bg, fg = colors
    return f'<span class="sa-badge" style="background:{bg};color:{fg}">{html.escape(prefix + text)}</span>'


@st.cache_resource
def data_source():
    return get_data_source()


@st.cache_data(ttl=300, show_spinner="Loading tickets...")
def load_data():
    source = data_source()
    tickets = source.list_tickets()
    results = source.list_results(ALL_RESULT_COLUMNS)
    articles = {a.article_id: a for a in source.list_articles()}
    return tickets, results, articles


def stats_bar(s: dict) -> None:
    items = [(s["tickets"], "tickets", GRAY), (s["escalations"], "escalations", URGENCY["urgent"]),
             (s["needs_person"], "need a person", URGENCY["high"]), (s["drafts"], "drafts ready", URGENCY["low"])]
    cells = "".join(f'<div class="sa-stat" style="background:{bg};color:{fg}"><div class="n">{n}</div>'
                    f'<div class="l">{label}</div></div>' for n, label, (bg, fg) in items)
    st.markdown(f'<div class="sa-stats">{cells}</div>', unsafe_allow_html=True)


def ticket_label(v) -> str:
    dot = DOT.get(v.ai["ai_urgency"], "gray")
    flag = " · needs a person" if v.needs_person else ""
    return f":{dot}[●] **{v.ticket.ticket_id}** {v.ticket.subject}  \n:gray[{v.ai['ai_urgency'] or 'not triaged'} · {v.ai['ai_queue'] or '-'}{flag}]"


def main() -> None:
    st.set_page_config(page_title="Storely Agent Assist", page_icon="🛍️", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)
    if "saved" in st.session_state:
        st.toast(st.session_state.pop("saved"), icon="✅")
    tickets, results, articles = load_data()
    views = build_views(tickets, results)

    st.markdown(f'<div class="sa-header"><b>Storely Agent Assist</b><span>AI triage and draft replies · '
                f'data from {html.escape(data_source().name)}</span></div>', unsafe_allow_html=True)
    stats_bar(summary(views))

    with st.sidebar:
        st.subheader("Tickets")
        text = st.text_input("Search", placeholder="Ticket, subject, merchant...")
        queues = st.multiselect("Queue", sorted({v.ai["ai_queue"] for v in views if v.ai["ai_queue"]}))
        urgencies = st.multiselect("Urgency", ["urgent", "high", "medium", "low"])
        only_person = st.checkbox("Only tickets that need a person")
        shown = filter_views(views, queues, urgencies, only_person, text)
        st.caption(f"{len(shown)} of {len(views)} tickets, most urgent first")
        if not shown:
            st.info("No tickets match these filters.")
            return
        ids = [v.ticket.ticket_id for v in shown]
        picked = st.radio("Ticket", ids, format_func=lambda i: ticket_label(next(v for v in shown if v.ticket.ticket_id == i)),
                          label_visibility="collapsed")
        if st.button("Reload data", help="Read the latest data again"):
            load_data.clear()
            st.rerun()

    v = next(v for v in shown if v.ticket.ticket_id == picked)
    show_ticket(v, articles)


def show_ticket(v, articles) -> None:
    t, ai = v.ticket, v.ai
    left, right = st.columns([1, 1], gap="medium")

    with left:
        st.markdown(f'<div class="sa-card"><div class="sa-label">{html.escape(t.ticket_id)}</div>'
                    f'<h3>{html.escape(t.subject)}</h3><div class="sa-meta">{html.escape(t.customer_name)} · '
                    f'{html.escape(t.store_name)} · {html.escape(t.plan)} plan · {html.escape(t.channel)} · '
                    f'{html.escape(t.created_at)}</div><div class="sa-body">{html.escape(t.body)}</div></div>',
                    unsafe_allow_html=True)
        if v.escalated:
            st.error("**Priority Escalation.** Urgent, or an angry merchant at high risk of leaving. Handle first.")
        if ai["ai_category"]:
            badges = "".join([
                badge(ai["ai_category"], CATEGORY),
                badge(ai["ai_urgency"], URGENCY.get(ai["ai_urgency"], GRAY), "urgency: "),
                badge(ai["ai_sentiment"], SENTIMENT.get(ai["ai_sentiment"], GRAY)),
                badge(ai["ai_churn_risk"], CHURN.get(ai["ai_churn_risk"], GRAY), "churn: "),
                badge(ai["ai_queue"], QUEUE.get(ai["ai_queue"], GRAY), "→ "),
            ])
            st.markdown(f'<div class="sa-card"><div class="sa-label">AI triage</div><div class="sa-badges">{badges}'
                        f'</div><div class="sa-meta">Why: {html.escape(ai["ai_reason"])}</div></div>',
                        unsafe_allow_html=True)
        else:
            st.info("Not triaged yet. Run: python -m scripts.run_triage")

    with right:
        st.markdown('<div class="sa-label">Reply</div>', unsafe_allow_html=True)
        if not ai["ai_reply"]:
            st.info("No draft reply yet. Run: python -m scripts.run_answers")
        if ai["ai_answered"] == "no":
            st.warning(f"**The AI didn't find the answer in the help articles**, so this needs a person.  \n"
                       f"Missing: {ai['ai_missing']}")
        if ai["agent_status"]:
            colors = URGENCY["low"] if ai["agent_status"] == READY else URGENCY["high"]
            st.markdown(badge(ai["agent_status"], colors, "Agent: "), unsafe_allow_html=True)
        text = st.text_area("Draft reply (you can edit it)", v.reply_text, height=320, key=f"reply-{t.ticket_id}")

        b1, b2, _ = st.columns([1, 1, 1])
        if b1.button("Save reply", key="save", use_container_width=True):
            save(t.ticket_id, text, READY)
        if b2.button("Needs a person", key="person", use_container_width=True):
            save(t.ticket_id, text, NEEDS_PERSON)
        if ai["agent_reply"] and ai["agent_reply"] != ai["ai_reply"]:
            with st.expander("Compare with the AI's original draft"):
                st.text(ai["ai_reply"])

        if v.source_ids:
            st.markdown('<div class="sa-label">Sources the reply is based on</div>', unsafe_allow_html=True)
            for sid in v.source_ids:
                article = articles.get(sid)
                with st.expander(f"📄 {sid} {article.title if article else ''}"):
                    st.markdown(article.body if article else "This article was not found.")


def save(ticket_id: str, text: str, status: str) -> None:
    data_source().write_agent(ticket_id, {"agent_reply": text, "agent_status": status})
    load_data.clear()
    st.session_state["saved"] = f"Saved {ticket_id}: {status}"
    st.rerun()


main()
