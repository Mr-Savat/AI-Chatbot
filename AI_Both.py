import streamlit as st
import os
import openai
from googleapiclient.discovery import build
from dotenv import load_dotenv
import csv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEARCH_API_KEY = os.getenv("GOOGLE_SEARCH_API_KEY")
SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")

if not OPENAI_API_KEY:
    st.error("OPENAI_API_KEY environment variable not set.")
if not SEARCH_API_KEY:
    st.warning("SEARCH_API_KEY environment variable not set. Search functionality will be limited.")
if not SEARCH_ENGINE_ID:
    st.warning("SEARCH_ENGINE_ID environment variable not set. Search functionality will be limited.")

openai.api_key = OPENAI_API_KEY

def load_faq(filepath="faq.csv"):
    faq = {}
    try:
        with open(filepath, mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if len(row) == 2:
                    question, answer = row
                    faq[question.lower()] = answer
    except FileNotFoundError:
        st.warning(f"Warning: FAQ file '{filepath}' not found.")
    return faq

def find_faq_answer(question, faq):
    question_lower = question.lower()
    if question_lower in faq:
        return faq[question_lower]
    return None

def generate_openai_response(prompt):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",  # Change Model to gpt-4o-mini
            messages=[
                {"role": "system", "content": "You are a helpful FAQ chatbot."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating OpenAI response: {e}")
        return "Sorry, I encountered an error. Please try again later."

def search_google(query):
    if not SEARCH_API_KEY or not SEARCH_ENGINE_ID:
        return "Search functionality is disabled."
    try:
        service = build("customsearch", "v1", developerKey=SEARCH_API_KEY)
        response = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        results = response.get("items", [])
        if results:
            return results[0]["snippet"]
        else:
            return "No relevant search results found."
    except Exception as e:
        st.error(f"Error during Google search: {e}")
        return "Sorry, I encountered an error during search."

def main():
    st.title("AI Chatbot for FAQs")
    faq = load_faq()

    if 'chat_history' not in st.session_state:
        st.session_state['chat_history'] = []

    user_input = st.text_input("Ask a question:")

    if user_input:
        st.session_state['chat_history'].append(f"User: {user_input}")
        faq_answer = find_faq_answer(user_input, faq)

        if faq_answer:
            response = faq_answer
        else:
            openai_response = generate_openai_response(user_input)
            if "I don't know" in openai_response:
                search_result = search_google(user_input)
                response = f"I am not sure, but here is what I found on the web: {search_result}"
            else:
                response = openai_response

        st.session_state['chat_history'].append(f"Bot: {response}")

        for message in st.session_state['chat_history']:
            st.text(message)

if __name__ == "__main__":
    main()