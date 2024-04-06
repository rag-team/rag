import os
import time

from fastapi import FastAPI, UploadFile, File, Response
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp

from db import VectorStore

app = FastAPI()


@app.on_event("startup")
def startup_event():
    model_path = "./models/tinyllama-1.1b-chat-v0.3.Q2_K.gguf"
    print("Loading LlamaCpp model...")
    start = time.time()
    app.state.llm = LlamaCpp(
        model_path=model_path,
        temperature=0.5,
        verbose=False,
        n_ctx=2048,
    )
    end = time.time()
    print(f"LlamaCpp model loaded in {end - start} seconds")

    print("Loading VectorStore...")
    start = time.time()
    app.state.vectorstore = VectorStore()
    end = time.time()
    print(f"VectorStore loaded in {end - start} seconds")

    app.state.chain = ConversationalRetrievalChain.from_llm(
        llm=app.state.llm,
        retriever=app.state.vectorstore.get_store().as_retriever(search_k=5),
        memory=ConversationBufferMemory(memory_key="chat_history", return_messages=True),
        # return_source_documents=True,
    )


@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure the directory for storing files exists, if not create it
        os.makedirs("uploads", exist_ok=True)

        # Save the uploaded file to the "uploads" directory with the original name
        with open(os.path.join("uploads", file.filename), "wb") as buffer:
            buffer.write(await file.read())
        app.state.vectorstore.injest_files(files=["uploads/" + file.filename])

        return Response(content=f"File {file.filename} uploaded successfully", status_code=200)
    except Exception as e:
        return Response(content=f"Failed to upload file: {e}", status_code=500)


@app.get("/chat/")
async def chat(query: str):
    response = app.state.chain(query)
    return response["answer"]
