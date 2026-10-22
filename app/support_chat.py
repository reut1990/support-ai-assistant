"""Support chat for merchants: answers from the help articles, or hands the conversation to a person.

Run it from the project folder:
    python -m streamlit run app/support_chat.py

It starts in free practice mode (a fake AI, no API calls). Real answers from Claude cost about $0.0007 per message.
Every chat ends as a ticket: in HubSpot when DATA_SOURCE=hubspot, otherwise in data/output/chat_tickets.csv.
"""

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so "src" can be imported when run by Streamlit

import streamlit as st

from src.answer.engine import Answerer
from src.answer.fake_client import FakeAnswerClient
from src.chat.agent import MAX_COST_PER_CHAT, ChatAgent, ChatSession, Merchant
from src.chat.prompt import SYSTEM_PROMPT
from src.chat.tickets import chat_tickets
from src.connectors import get_data_source
from src.triage.engine import Triager
from src.triage.fake_client import FakeClaudeClient

PLANS = ["Basic", "Grow", "Advanced"]
CSS = """
<style>
.block-container {padding-top: 2.6rem; max-width: 820px;}
.sc-header {background: #1e4fa8; color: #fff; border-radius: 8px; padding: 14px 18px; margin-bottom: 14px;}
.sc-header b {font-size: 1.3rem;}
.sc-header span {opacity: .85; margin-left: 10px;}
.sc-source {font-size: .85rem; color: #5b6575; margin-top: 6px;}
.sc-end {border-radius: 8px; padding: 12px 16px; margin-top: 8px;}
.st-key-solved button {background: #16a34a; border-color: #16a34a; color: #fff;}
.st-key-solved button:hover {background: #15803d; border-color: #15803d; color: #fff;}
.st-key-person button {background: #f59e0b; border-color: #f59e0b; color: #1d2430;}
.st-key-person button:hover {background: #d97706; border-color: #d97706; color: #1d2430;}
</style>
"""


@st.cache_resource
def articles():
    return get_data_source().list_articles()


@st.cache_resource
def ticket_store():
    return chat_tickets()


def agent(fake: bool) -> ChatAgent:
    if fake:
        triager = Triager(client=FakeClaudeClient())
        answerer = Answerer(articles(), client=FakeAnswerClient(), system_prompt=SYSTEM_PROMPT)
    else:
        triager = Triager()
        answerer = Answerer(articles(), system_prompt=SYSTEM_PROMPT)
    return ChatAgent(triager, answerer, ticket_store())


def sidebar() -> bool:
    with st.sidebar:
        st.subheader("Chat settings")
        fake = st.toggle("Free practice mode (fake AI)", value=True,
                         help="On: template answers, no API calls, $0. Off: real answers from Claude.")
        if fake:
            st.caption("Practice mode: nothing is charged.")
        else:
            st.warning(f"Real AI: about $0.0007 per message. A chat stops itself at ${MAX_COST_PER_CHAT:.2f}.")
        session = st.session_state.get("chat")
        if session:
            st.metric("Cost of this chat", f"${session.cost_usd:.4f}")
            if session.triage:
                t = session.triage
                st.caption(f"Triage: {t['ai_category']} · {t['ai_urgency']} · {t['ai_sentiment']} · "
                           f"churn {t['ai_churn_risk']} → {t['ai_queue']}")
        st.caption(f"Finished chats are saved to: {ticket_store().name}")
        if st.button("Start a new chat"):
            st.session_state.pop("chat", None)
            st.rerun()
    return fake


def start_form() -> None:
    st.markdown("Please tell us who you are, so we can help with your store.")
    with st.form("start"):
        name = st.text_input("Your name", placeholder="Maya Larsen")
        email = st.text_input("Email", placeholder="maya@example.com")
        store = st.text_input("Store name", placeholder="Nomad Market")
        plan = st.selectbox("Storely plan", PLANS)
        if st.form_submit_button("Start chat", type="primary"):
            if not name.strip() or "@" not in email:
                st.error("Please enter your name and a valid email address.")
                return
            st.session_state["chat"] = ChatSession(Merchant(name.strip(), email.strip(), store.strip(), plan))
            st.rerun()


def show_messages(session: ChatSession) -> None:
    with st.chat_message("assistant", avatar="🛍️"):
        st.write(f"Hello {session.merchant.first_name}, welcome to Storely Support. How can I help you today?")
    for m in session.messages:
        with st.chat_message("user" if m.role == "merchant" else "assistant",
                             avatar="🧑" if m.role == "merchant" else "🛍️"):
            st.markdown(m.text.replace("\n", "  \n"))
            if m.sources:
                titles = ", ".join(f"“{html.escape(a.title)}”" for a in m.sources)
                st.markdown(f'<div class="sc-source">For more details, see our help article {titles}.</div>',
                            unsafe_allow_html=True)


def show_end(session: ChatSession) -> None:
    if session.status == "resolved":
        st.markdown(f'<div class="sc-end" style="background:#dcfce7;color:#16653a"><b>Chat closed, solved by the AI.'
                    f'</b> Saved as closed ticket {html.escape(session.ticket_id)} for reporting.</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="sc-end" style="background:#ffedd5;color:#9a4a00"><b>Handed to a person.</b> '
                    f'New ticket {html.escape(session.ticket_id)} created with the full conversation. '
                    f'Reason: {html.escape(session.handoff_reason)}</div>', unsafe_allow_html=True)


def main() -> None:
    st.set_page_config(page_title="Storely Support Chat", page_icon="💬", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="sc-header"><b>Storely Support</b><span>Chat with our assistant</span></div>',
                unsafe_allow_html=True)
    fake = sidebar()
    session = st.session_state.get("chat")
    if session is None:
        start_form()
        return

    chat = agent(fake)
    show_messages(session)
    if session.awaiting_feedback:
        prompt = ("Did this solve your problem? You can also ask a follow-up question."
                  if not session.offer_person else
                  "If this still doesn't solve it, I can connect you with a specialist.")
        st.caption(prompt)
        c1, c2, _ = st.columns([1, 1.3, 1])
        if c1.button("Yes, that solved it", key="solved", use_container_width=True):
            chat.resolve(session)
            st.rerun()
        if c2.button("No, talk to a person", key="person", use_container_width=True):
            chat.hand_off(session, "not_solved")
            st.rerun()
    if not session.is_open:
        show_end(session)
        return
    text = st.chat_input("Type your message")
    if text:
        with st.spinner("Thinking..."):
            chat.handle(session, text)
        st.rerun()


main()
