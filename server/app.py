
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter

from db import VectorStore


# pdf docs are uploaded files

def get_pdf_text():
    # read bible from text file
    with open("bible.txt", "r") as bible:
        text = bible.read()
    return text


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
    chunks = text_splitter.split_text(text)
    return chunks


def get_conversation_chain(vectorestore):
    # Use open source LLama language model from huggingface
    model_path = "server/models/llama-2-7b-chat.Q5_K_M.gguf"
    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.5,
        verbose=False,
        n_ctx=2048,
    )

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorestore.as_retriever(search_k=5),
        memory=memory,
        # return_source_documents=True,
    )

    return conversation_chain


vectorstore = VectorStore().store

raw_text = get_pdf_text()  # get pdf text
text_chunks = get_text_chunks(raw_text)  # get the text chunks
vectorstore.add_texts(text_chunks, verbose=True)

chain = get_conversation_chain(vectorstore)
chain({'question': "Who is Judha?"})

