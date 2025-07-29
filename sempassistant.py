
import streamlit as st
import openai
import csv
from datetime import datetime
from pathlib import Path

st.set_page_config(page_title="SEMPAssistant", page_icon="🩺", layout="centered")
st.title("👋 Welcome to SEMPAssistant!")
st.write("I'm here to help you with SEMPA membership and event questions. Ask me anything!")

FAQS = {
    "join sempa": "Visit the Join or Renew page at sempa.org and choose 'Join' to create your account.",
    "renew membership": "Log in to your SEMPA Member Portal and follow the renewal instructions.",
    "membership categories": "SEMPA offers categories like standard, senior fellow, and more — details at sempa.org/join-or-renew.",
    "register for events": "Go to the Event Calendar or Education sections at sempa.org to register for events like SEMPA 360.",
    "member discounts": "Yes! Members save up to 40% on events, CME, and partner resources.",
    "access session recordings": "Log in to your SEMPA account and go to the 'My Education' section to find session recordings.",
    "contact sempa": "You can reach SEMPA at sempa@sempa.org or call 877-297-7954."
}

def normalize(text):
    return text.lower().strip()

def match_faq(user_input):
    norm_input = normalize(user_input)
    for key, response in FAQS.items():
        if all(word in norm_input for word in key.split()):
            return response
    return None

def log_token_usage(question, total_tokens):
    cost_per_token = 0.002 / 1000
    est_cost = round(total_tokens * cost_per_token, 6)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("token_log.csv", mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, question, total_tokens, est_cost])

user_input = st.text_input("Ask a question about SEMPA membership or events:")

if user_input:
    answer = match_faq(user_input)
    if answer:
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
            st.success(gpt_answer)
        except Exception as e:
            st.error("Sorry, something went wrong while contacting OpenAI.")

# Admin-only sidebar tools
st.sidebar.markdown("🔐 Admin Panel")
if st.sidebar.checkbox("Show Admin Tools"):
    if Path("token_log.csv").exists():
        with open("token_log.csv", "rb") as f:
            st.download_button("📥 Download Token Log", f, file_name="token_log.csv")
