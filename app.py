import streamlit as st
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_text_splitters import CharacterTextSplitter
import pypdfium2 as pdfium  # Check leaderboard here: https://github.com/py-pdf/benchmarks  # yiwei-ang:feature/pdfium

from db import VectorStore
from templates import css, bot_template, user_template


# pdf docs are uploaded files

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = pdfium.PdfDocument(pdf)
        for i in range(len(pdf_reader)):
            page = pdf_reader.get_page(i)
            textpage = page.get_textpage()
            text += textpage.get_text_range() + "\n"
    return text


def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(separator="\n", chunk_size=5000, chunk_overlap=500, length_function=len)
    chunks = text_splitter.split_text(text)
    return chunks


def get_conversation_chain(vectorestore):
    # Use open source LLama language model from huggingface
    model_path = "models/llama-2-7b-chat.Q5_K_M.gguf"


    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.75,
        verbose=False,
        max_length=512,
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorestore.as_retriever(),
        memory=memory,
        #return_source_documents=True,
    )

    return conversation_chain


def save_question_and_clear_prompt(ss):
    ss.user_question = ss.prompt_bar
    ss.prompt_bar = ""  # clearing the prompt bar after clicking enter to prevent automatic re-submissions

def write_chat(msgs):  # Write the Q&A in a pretty chat format
    for i, msg in enumerate(msgs):
        if i % 2 == 0:  # it's a question
            st.write(user_template.replace("{{MSG}}", msg.content), unsafe_allow_html=True)
        else:  # it's an answer
            st.write(bot_template.replace("{{MSG}}", msg.content), unsafe_allow_html=True)

def handle_user_input(user_prompt):
    response = st.session_state.conversation({"question": user_prompt})
    print(response)
    st.session_state.chat_history = response["chat_history"]

    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            st.write(user_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)
        else:
            st.write(bot_template.replace("{{MSG}}", message.content), unsafe_allow_html=True)


def main():
    ss = st.session_state

    # Page design
    st.set_page_config(page_title="AI Document Search", page_icon=":robot_face:", layout="wide")
    st.write(css, unsafe_allow_html=True)
    st.header("AI Document Search :robot_face:")

    # Initializing session state variables
    if "conversation_chain" not in ss:
        print(ss)
        vectorstore = VectorStore().store
        ss.conversation_chain = get_conversation_chain(vectorstore)  # create conversation chain

    if "prompt_bar" not in ss:
        ss.prompt_bar = ""
    if "user_question" not in ss:
        ss.user_question = ""
    if "docs_are_processed" not in ss:
        ss.docs_are_processed = False

    # add a sidebar to upload files (only pdf)
    with st.sidebar:
        st.subheader("Datei-Upload")
        pdf_docs = st.file_uploader("Upload your PDFs here and click 'Process'", accept_multiple_files=True, type="pdf")
        if st.button("Process") and pdf_docs:
            with st.spinner("Verarbeite Dokumente..."):
                raw_text = get_pdf_text(pdf_docs)  # get pdf text
                text_chunks = get_text_chunks(raw_text)  # get the text chunks
                vectorstore = VectorStore().store
                vectorstore.add_texts(text_chunks, verbose=True)

                ss.docs_are_processed = True
        if ss.docs_are_processed:
            st.success("Dokumente erfolgreich verarbeitet")

    st.text_input("Ask a question here:", key='prompt_bar', on_change=save_question_and_clear_prompt(ss))

    if ss.user_question:
        ss.conversation_chain({'question': ss.user_question})  # This is what gets the response from the LLM!
        if hasattr(ss.conversation_chain.memory, 'chat_memory'):
            chat = ss.conversation_chain.memory.chat_memory.messages
            write_chat(chat)

    if hasattr(ss.conversation_chain, 'memory'):  # There is memory if the documents have been processed
        if hasattr(ss.conversation_chain.memory, 'chat_memory'):  # There is chat_memory if questions have been asked
            if st.button("Forget conversation"):  # adding a button
                ss.conversation_chain.memory.chat_memory.clear()  # clears the ConversationBufferMemory


if __name__ == "__main__":
    main()
