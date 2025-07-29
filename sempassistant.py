import streamlit as st
import openai
import csv
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="SEMPAssistant", page_icon="🩺", layout="centered")
st.title("👋 Welcome to SEMPAssistant!")
st.write("I'm here to help you with SEMPA membership and event questions. Ask me anything!")

# FAQs
FAQS = {
    "join or renew": "Visit the [Join or Renew page](https://sempa.site-ym.com/general/register_member_type.asp) to get started with SEMPA membership.",
    "membership categories": "SEMPA offers various membership categories. You can view them all at [https://sempa.org/categories-dues/](https://sempa.org/categories-dues/).",
    "register for events": "Go to the Event Calendar or Education sections at sempa.org to register for events like SEMPA 360.",
    "member discounts": "Yes! Members save up to 40% on events, CME, and partner resources.",
    "access session recordings": "Log in to your SEMPA account and go to the 'My Education' section to find session recordings.",
    "contact sempa": "You can reach SEMPA at sempa@sempa.org or call 877-297-7954."
}

# Synonym map to enhance FAQ detection
SYNONYM_MAP = {
    "join or renew": ["join", "sign up", "enroll", "become a member", "renew", "renewal", "extend membership"],
    "membership categories": ["categories", "types", "levels", "dues", "cost", "pricing"],
    "register for events": ["register", "sign up", "attend", "enroll", "conference"],
    "member discounts": ["discount", "save", "benefits", "perks"],
    "access session recordings": ["recordings", "sessions", "videos", "past sessions", "on demand"],
    "contact sempa": ["contact", "email", "call", "support", "help"]
}

def normalize(text):
    return text.lower().strip()

def match_faq(user_input):
    norm_input = normalize(user_input)
    for faq_key, synonyms in SYNONYM_MAP.items():
        if any(s in norm_input for s in synonyms):
            return FAQS[faq_key], "FAQ"
    return None, None

def detect_agent_request(user_input):
    norm_input = normalize(user_input)
    trigger_words = ["agent", "representative", "someone live", "talk to", "speak with"]
    return any(word in norm_input for word in trigger_words)

def log_token_usage(question, total_tokens):
    cost_per_token = 0.002 / 1000
    est_cost = round(total_tokens * cost_per_token, 6)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("token_log.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, question, total_tokens, est_cost])

def log_source(question, source):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("source_log.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, question, source])

user_input = st.text_input("Ask a question about SEMPA membership or events:")

if user_input:
    if detect_agent_request(user_input):
        st.info("📧 The SEMPA support team is not available for live chat, but if you type your question here we'll get right back to you via email.")
        st.markdown("[Click here to email us directly](mailto:sempa@sempa.org)")
        log_source(user_input, "Email Referral")
    else:
        answer, source = match_faq(user_input)
        if answer:
            log_source(user_input, source)
            st.success(answer)
        else:
            openai.api_key = st.secrets["OPENAI_API_KEY"]
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant for SEMPA (Society of Emergency Medicine PAs). Only answer questions about SEMPA membership, events, or support. If unsure, suggest the user contact sempa@sempa.org."},
                        {"role": "user", "content": user_input}
                    ]
                )
                gpt_answer = response['choices'][0]['message']['content']
                total_tokens = response['usage']['total_tokens']
                log_token_usage(user_input, total_tokens)
                log_source(user_input, "GPT")
                st.success(gpt_answer)
            except Exception:
                log_source(user_input, "Fallback")
                st.info("I'm not sure — please contact us at [sempa@sempa.org](mailto:sempa@sempa.org)")

# Admin tools in sidebar
st.sidebar.markdown("🔐 Admin Panel")
if st.sidebar.checkbox("Show Admin Tools"):
    if Path("token_log.csv").exists():
        with open("token_log.csv", "rb") as f:
            st.download_button("📥 Download Token Log", f, file_name="token_log.csv")
    if Path("source_log.csv").exists():
        with open("source_log.csv", "rb") as f:
            st.download_button("📥 Download Source Log", f, file_name="source_log.csv")

