import asyncio
import time
import streamlit as st
import threading


def upload_files(files):
    # wait for 3 seconds
    time.sleep(3)
    pass


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
                    ss.docs_are_processed = True
            if ss.docs_are_processed:
                st.toast('Dokumene wurden erfolgreich hochgeladen.')

    prompt = st.text_input("Ask a question here:")

    if prompt:
        ss.conversation_chain.append({"role": "user", "content": prompt})
        thread = threading.Thread(target=run_send_prompt, args=(prompt,))
        thread.start()

    update_chat()



if __name__ == "__main__":
    main()
