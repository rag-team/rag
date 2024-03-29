import asyncio
import time

import requests
import streamlit as st
import threading


def upload_files(files):
    # Send files to FastAPI server
    url = "http://localhost:8000/upload-file/"
    success_count = 0
    error_messages = []

    for file in files:
        filename = file.name
        mime_type = file.type
        file_data = {"file": (filename, file.getvalue(), mime_type)}
        response = requests.post(url, files=file_data)
        if response.status_code == 200:
            success_count += 1
        else:
            error_messages.append(f"Failed to upload '{filename}': {response.text}")

    if success_count == len(files):
        st.success("All files uploaded successfully")
    elif success_count == 0:
        st.error("Failed to upload all files")
    else:
        st.warning("Some files uploaded successfully, but there were errors for others")
        for error_message in error_messages:
            st.error(error_message)



async def send_prompt(prompt: str):
    # For demonstration, let's mock AI response
    await asyncio.sleep(2)
    response = "AI: This is the AI response to: " + prompt
    st.session_state.conversation_chain.append({"role": "ai", "content": response})


def update_chat():
    for i, msg in enumerate(st.session_state.conversation_chain):
        if i % 2 == 0:
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("ai"):
                st.write(msg["content"])


def run_send_prompt(prompt):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(send_prompt(prompt))


def main():
    ss = st.session_state

    # Page design
    st.set_page_config(page_title="AI Document Search", page_icon=":robot_face:", layout="wide")
    st.header("AI Document Search :robot_face:")

    # Initializing session state variables
    if "conversation_chain" not in ss:
        ss.conversation_chain = []

    if "user_question" not in ss:
        ss.user_question = ""

    if "docs_are_processed" not in ss:
        ss.docs_are_processed = False

    # add a sidebar to upload files (only pdf)
    with st.sidebar:
        st.subheader("Datei-Upload")
        if not ss.docs_are_processed:
            pdf_docs = st.file_uploader("Upload your PDFs here and click 'Process'", accept_multiple_files=True,
                                        type="pdf")
            if st.button("Process") and pdf_docs:
                with st.spinner("Verarbeite Dokumente..."):
                    upload_files(pdf_docs)

    prompt = st.text_input("Ask a question here:")

    if prompt:
        ss.conversation_chain.append({"role": "user", "content": prompt})
        thread = threading.Thread(target=run_send_prompt, args=(prompt,))
        thread.start()

    update_chat()



if __name__ == "__main__":
    main()
