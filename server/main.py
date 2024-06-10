import io
import json
import os
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Response, UploadFile
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pypdf import PdfReader, PdfWriter

from server.schlagwortdb import models
from server.schlagwortdb.database import SessionLocal, engine
from server.vectordb import VectorStore

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    #"models/tinyllama-1.1b-chat-v0.3.Q4_K_M.gguf"
    #"models/llama-2-7b-chat.Q5_K_M.gguf"
    "models/leo-mistral-hessianai-7b-chat.Q5_K_M.gguf"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Loading {MODEL_PATH} LlamaCpp model...")
    start = time.time()
    app.state.llm = LlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.5,
        verbose=False,
        n_ctx=2048,
        n_gpu_layers=-1,
    )
    end = time.time()
    print(f"LlamaCpp model loaded in {end - start} seconds")

    print("Loading VectorStore...")
    start = time.time()
    app.state.vectorstore = VectorStore()
    end = time.time()
    print(f"VectorStore loaded in {end - start} seconds")

    yield


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan)

with open(os.path.join(os.path.dirname(__file__), "PROMPT.txt"), "r") as f:
    PROMPT = f.read()

with open(os.path.join(os.path.dirname(__file__), "context.json"), "r") as f:
    context = json.loads(f.read())


@app.get("/schlagworte/")
def get_schlagworte(db=Depends(get_db)):
    return db.query(models.Schlagwort).all()


@app.post("/schlagworte/create/")
def create_schlagwort(schlagwort: str, db=Depends(get_db)):
    schlagwort = models.Schlagwort(schlagwort=schlagwort)
    db.add(schlagwort)
    db.commit()
    return schlagwort


@app.get("/hw")
def hello_world():
    return {"hello": "world"}


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
    output = JsonOutputParser()
    chain = prompt | app.state.llm | output

    data = {
        "fields": {name: field.field_type for name, field in fields.items()},
        "context": json.dumps(context),
    }
    try:
        result = chain.invoke(data)
    except OutputParserException as e:
        raise HTTPException(
            500,
            {
                "error": "Failed to fill PDF because LLM too dumb.",
                "llm": os.path.basename(MODEL_PATH),
                "result": e.llm_output,
            },
        )

    # Write results to PDF
    writer = PdfWriter()
    writer.append(reader)
    writer.set_need_appearances_writer()

    for page in writer.pages:
        writer.update_page_form_field_values(page, result, auto_regenerate=False)

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
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # Specify the key to store in memory
        ),
        return_source_documents=True,
    )
    response = chain(query)

    # Extract the source documents
    source_documents = response.get("source_documents", [])

    # Print out the source documents
    for doc in source_documents:
        print("Documents", doc)

    # Return both answer and source documents
    return response["answer"]

