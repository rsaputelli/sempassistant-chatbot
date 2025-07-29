
import streamlit as st
import openai

st.set_page_config(page_title="SEMPAssistant", page_icon="🩺", layout="centered")

st.title("👋 Welcome to SEMPAssistant!")
st.write("I'm here to help you with SEMPA membership and event questions. Ask me anything!")

# FAQ knowledge base (hardcoded for now)
FAQS = {
    "how do i join sempa": "Visit the Join or Renew page at sempa.org and choose 'Join' to create your account.",
    "how do i renew my membership": "Log in to your SEMPA Member Portal and follow the renewal instructions.",
    "what are the membership categories": "SEMPA offers categories like standard, senior fellow, and more — details at sempa.org/join-or-renew.",
    "how can i register for sempa events": "Go to the Event Calendar or Education sections at sempa.org to register for events like SEMPA 360.",
    "do members get discounts": "Yes! Members save up to 40% on events, CME, and partner resources.",
    "how do i access session recordings": "Log in to your SEMPA account and go to the 'My Education' section to find session recordings.",
    "how do i contact sempa": "You can reach SEMPA at sempa@sempa.org or call 877-297-7954."
}

# Normalize function
def normalize(text):
    return text.lower().strip()

# Chat input
user_question = st.text_input("Ask a question about SEMPA membership or events:")

if user_question:
    normalized = normalize(user_question)
    answer = None
    for q, a in FAQS.items():
        if q in normalized:
            answer = a
            break
    if answer:
        st.success(answer)
    else:
        st.info("I'm not sure — please contact us at [sempa@sempa.org](mailto:sempa@sempa.org)")
