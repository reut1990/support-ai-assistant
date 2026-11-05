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
import streamlit.components.v1 as components

from src.answer.engine import Answerer
from src.answer.schema import ChatReply
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
.st-key-solved button {background: #16a34a; border-color: #16a34a; color: #fff;}
.st-key-solved button:hover {background: #15803d; border-color: #15803d; color: #fff;}
.st-key-person button {background: #f59e0b; border-color: #f59e0b; color: #1d2430;}
.st-key-person button:hover {background: #d97706; border-color: #d97706; color: #1d2430;}
</style>
"""


@st.cache_resource(show_spinner=False)
def articles():
    return get_data_source().list_articles()


@st.cache_resource(show_spinner=False)
def ticket_store():
    return chat_tickets()


@st.cache_resource(show_spinner=False)
def agent(fake: bool) -> ChatAgent:
    # Built once and shared: loading the help articles (from Google Drive when it's set up) and the AI client
    # takes a few seconds, so it happens while the merchant fills in the start form.
    if fake:
        triager = Triager(client=FakeClaudeClient())
        answerer = Answerer(articles(), client=FakeAnswerClient(), system_prompt=SYSTEM_PROMPT, output_format=ChatReply)
    else:
        triager = Triager()
        answerer = Answerer(articles(), system_prompt=SYSTEM_PROMPT, output_format=ChatReply)
    return ChatAgent(triager, answerer, ticket_store())


def sidebar() -> bool:
    with st.sidebar:
        st.subheader("Chat settings")
        fake = st.toggle("Free practice mode (fake AI)", value=True,
                         help="On: template answers, no API calls, $0. Off: real answers from Claude.")
        if fake:
            st.caption("Practice mode: nothing is charged.")
        else:
            st.warning(f"Real AI: about \\$0.0007 per message. A chat stops itself at \\${MAX_COST_PER_CHAT:.2f}.")
        session = st.session_state.get("chat")
        if session:
            st.metric("Cost of this chat", f"${session.cost_usd:.4f}")
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
            # Replies are laid out by src/chat/formatting.py. "$" is escaped so "$0 to $50" isn't read as math.
            st.markdown(m.text.replace("$", "\\$"))
            if m.sources:
                titles = [f"“{html.escape(a.title)}”" for a in m.sources]
                line = (f"our help article {titles[0]}" if len(titles) == 1 else
                        f"our help articles {', '.join(titles[:-1])} and {titles[-1]}")
                st.markdown(f'<div class="sc-source">For more details, see {line}.</div>', unsafe_allow_html=True)


def scroll_to_latest(session: ChatSession) -> None:
    """Streamlit redraws the page after every message, which can leave it scrolled up. Jump to the newest message."""
    components.html(f"""<script>
      // {len(session.messages)} messages: the number changes each time, so the script runs again
      const doc = window.parent.document;
      setTimeout(() => {{
        for (const sel of ['[data-testid="stMain"]', 'section.main', '[data-testid="stAppViewContainer"]']) {{
          const el = doc.querySelector(sel);
          if (el) el.scrollTo({{top: el.scrollHeight, behavior: "smooth"}});
        }}
        window.parent.scrollTo({{top: doc.body.scrollHeight, behavior: "smooth"}});
      }}, 150);
    </script>""", height=0)


def show_end(session: ChatSession) -> None:
    # What the merchant sees. Ticket numbers and handoff reasons are internal, so they stay in the demo panel.
    st.caption("This chat has ended. You can start a new chat at any time.")


def demo_panel(session: ChatSession) -> None:
    """Behind-the-scenes details for whoever is demoing the project. A real merchant would never see these."""
    with st.sidebar:
        st.divider()
        st.subheader("Behind the scenes")
        st.caption("Shown for the demo only. Merchants don't see this panel.")
        if session.triage:
            t = session.triage
            st.markdown(f"**Triage:** {t['ai_category']} · {t['ai_urgency']} · {t['ai_sentiment']} · "
                        f"churn {t['ai_churn_risk']} → {t['ai_queue']}")
        if session.status == "resolved":
            st.success(f"Solved by the AI. Saved as closed ticket {session.ticket_id}.")
        elif session.status == "handed_off":
            st.warning(f"Handed to a person. New ticket {session.ticket_id}. Reason: {session.handoff_reason}")
        if session.note_for_agent:
            st.info(f"Note for the agent: {session.note_for_agent}")


def main() -> None:
    st.set_page_config(page_title="Storely Support Chat", page_icon="💬", layout="centered")
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="sc-header"><b>Storely Support</b><span>Chat with our assistant</span></div>',
                unsafe_allow_html=True)
    fake = sidebar()
    session = st.session_state.get("chat")
    if session is None:
        start_form()
        agent(fake)  # load in the background of the form, so starting the chat is instant
        return

    show_messages(session)
    with st.spinner("Connecting you to Storely Support..."):
        chat = agent(fake)
    demo_panel(session)
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
    if session.awaiting_offer:
        c1, c2, _ = st.columns([1.3, 1, 1])
        if c1.button("Yes, connect me", key="person", use_container_width=True):
            chat.hand_off(session, "not_covered")
            st.rerun()
        if c2.button("No, thanks", key="decline", use_container_width=True):
            chat.decline_offer(session)
            st.rerun()
    if not session.is_open:
        scroll_to_latest(session)
        show_end(session)
        return
    scroll_to_latest(session)
    text = st.chat_input("Type your message")
    if text:
        # Show the merchant's message straight away, while the assistant works on the answer.
        with st.chat_message("user", avatar="🧑"):
            st.markdown(text.replace("$", "\\$"))
        with st.chat_message("assistant", avatar="🛍️"), st.spinner("Typing..."):
            chat.handle(session, text)
        st.rerun()


main()
