import io
import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Response, UploadFile
from langchain import ConversationalRetrievalChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pypdf import PdfReader, PdfWriter

from .db import VectorStore


@asynccontextmanager
async def lifespan():
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

    yield


app = FastAPI(lifespan=lifespan)

with open("PROMPT.txt", "r") as f:
    PROMPT = f.read()

with open("context.json", "r") as f:
    context = json.loads(f.read())


@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Ensure the directory for storing files exists, if not create it
        os.makedirs("uploads", exist_ok=True)

        # Save the uploaded file to the "uploads" directory with the original name
        with open(os.path.join("uploads", file.filename), "wb") as buffer:
            buffer.write(await file.read())
        app.state.vectorstore.injest_files(files=["uploads/" + file.filename])

        return Response(
            content=f"File {file.filename} uploaded successfully", status_code=200
        )
    except Exception as e:
        return Response(content=f"Failed to upload file: {e}", status_code=500)


@app.post("/fill-pdf/")
async def fill_pdf(file: UploadFile = File(...), context: dict = {}):
    bio = io.BytesIO(file.file.read())
    reader = PdfReader(bio)
    fields = reader.get_fields()

    prompt = ChatPromptTemplate.from_template(PROMPT)
    output = StrOutputParser()
    chain = prompt | app.state.llm | output

    data = {
        "fields": {name: field.field_type for name, field in fields.items()},
        "context": json.dumps(context),
    }
    result = chain.invoke(data)

    result_json = json.loads(result)
    writer = PdfWriter()
    writer.append(reader)
    writer.set_need_appearances_writer()

    for page in writer.pages:
        writer.update_page_form_field_values(page, result_json, auto_regenerate=False)

    bio = io.BytesIO()
    writer.write(bio)
    filled_pdf = bio.getvalue()

    filled_filename = file.filename.replace(".pdf", "_filled.pdf")
    headers = {"Content-Disposition": f"attachment; filename={filled_filename}"}
    return Response(filled_pdf, media_type="application/pdf", headers=headers)


@app.get("/chat/")
async def chat(query: str):
    chain = ConversationalRetrievalChain.from_llm(
        llm=app.state.llm,
        retriever=app.state.vectorstore.get_store().as_retriever(search_k=5),
        memory=ConversationBufferMemory(
            memory_key="chat_history", return_messages=True
        ),
        # return_source_documents=True,
    )
    response = chain(query)
    return response["answer"]
