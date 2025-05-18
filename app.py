import os
import dotenv
import streamlit as st
from gitingest import ingest
from google import genai
from google.genai import types

dotenv.load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Set up Gemini API
client = genai.Client(api_key=API_KEY)

st.set_page_config(page_title="GitHub Repo Q&A", layout="wide")
st.title("📘 GitHub Repo Agent")

# System instruction for the AI model
system_instruction = """You are a helpful AI agent that assists users in understanding GitHub repositories.
Your job is to explain the purpose, structure, and key components of the repository in a clear and concise manner.
Use developer-friendly language, and provide summaries and technical insights that would help a developer quickly understand the repo."""

# GitHub URL input
github_url = st.text_input("Enter GitHub Repository URL", placeholder="https://github.com/user/repo")

if st.button("Ingest and Summarize"):
    with st.spinner("Ingesting the repository..."):
        summary, tree, content = ingest(github_url, output='content.txt')

        with open("content.txt", 'r') as f:
            text = f.read()
        doc_data = text.encode('utf-8')

        prompt = """You are given the full source code and documentation of a GitHub repository.
Provide a high-level technical summary of the project. Always keep it short and crisp. Mention:
- The main purpose or functionality of the project.
- Key technologies and programming languages used.
- The structure of the codebase (important directories or files).
- Any setup instructions or usage info found in the repo.
- Any notable or unique features."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                types.Part(text=system_instruction),
                types.Part.from_bytes(data=doc_data, mime_type='text/plain'),
                types.Part(text=prompt)
            ],
            config=types.GenerateContentConfig(max_output_tokens=1500))
        summary_text = response.text

        st.success("Summary generated!")
        st.subheader("🔍 Summary")
        st.write(summary_text)

        # Save content and summary for reuse
        st.session_state.tree = tree
        st.session_state.doc_data = doc_data
        st.session_state.full_text = text
        st.session_state.summary_text = summary_text

# Q&A interface
if "doc_data" in st.session_state:
    st.subheader("💬 Ask Questions about the Repo")
    user_question = st.text_input("Your question:")
    if st.button("Ask"):
        if user_question.strip():
            qa_prompt = f"""Based on the following GitHub repository content, answer this question in a clear and developer-friendly way:\n\nQuestion: {user_question}"""

            qa_response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part(text=system_instruction),
                    types.Part.from_bytes(data=st.session_state.doc_data, mime_type='text/plain'),
                    types.Part(text=qa_prompt)
                ],
                config=types.GenerateContentConfig(max_output_tokens=1000))
            answer = qa_response.text
            st.markdown("**Answer:**")
            st.write(answer)

