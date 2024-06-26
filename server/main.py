import io
import json
import logging
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

import torch
from fastapi import Depends, FastAPI, File, HTTPException, Query, Response, UploadFile
from fastapi.responses import FileResponse
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.llms import LlamaCpp
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from pypdf import PdfReader, PdfWriter

from server.loggers import splitOutErrLogger
from server.personendatendb import models as nutzer_models
from server.personendatendb.database import SessionLocal as NutzerDBSessionLocal
from server.schlagwortdb import models
from server.schlagwortdb.database import SessionLocal, engine
from server.vectordb import VectorStore

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    # "models/tinyllama-1.1b-chat-v0.3.Q4_K_M.gguf"
    "models/llama-2-13b.gguf"
    # "models/leo-mistral-hessianai-7b-chat.Q5_K_M.gguf"
    #"models/chat-llama-3.gguf"
)

logger = splitOutErrLogger(
    "/server_data/Logs/WSpeicher_Archiv.log",
    "/server_data/Logs/WSpeicher_Error.log",
    name=__name__,
    level=logging.INFO,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Is CUDA available? ", torch.cuda.is_available())
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


def get_nutzer_db():
    db = NutzerDBSessionLocal()
    try:
        yield db
    finally:
        db.close()


# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan)
app.state.previous_id = None
### Statefully manage chat history ###
app.state.store = {}

with open(os.path.join(os.path.dirname(__file__), "PROMPT.txt"), "r") as f:
    PROMPT = f.read()

with open(os.path.join(os.path.dirname(__file__), "context.json"), "r") as f:
    context = json.loads(f.read())

for dir in ["_Dokumentendump_", "Archiv", "Conf", "Logs"]:
    dir = os.path.join("/", "server_data", dir)
    os.makedirs(dir, exist_ok=True)


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


def get_field_mapping(keywords: dict, fields: dict):
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
             You are a helpful assistant who matches inputs to keywords. A user will
             give you a list of inputs, and you have to respond which keywords the
             inputs belong to. If an input doesn't belong to any keyword, respond with
             `None`. Important: always respond in JSON format.
             Here is a list of keywords: {keywords}
             """,
            ),
            ("user", f"{fields}"),
        ]
    )
    output = StrOutputParser()  # JsonOutputParser()
    chain = prompt | app.state.llm | output

    data = {"keywords": ", ".join(keywords), "words": ",".join(fields)}
    result = chain.invoke(data)
    return result


@app.get("/get-document/")
async def get_document(
    doc_id: int, kunde_id: Optional[int] = Query(None), db=Depends(get_db)
):
    doc = db.query(models.DokumentLookup).get(doc_id)
    if not doc:
        raise HTTPException(404, {"error": "Document not found"})

    doc_file = os.path.join("/", "server_data", "Archiv", doc.docName)

    if not kunde_id:
        return FileResponse(doc_file, filename=doc.docOrigName)

    kunde = db.query(models.Kunde).get(kunde_id)
    if not kunde:
        raise HTTPException(404, {"error": "Kunde not found"})

    stammdaten = {
        "Anrede": kunde.anrede,
        "Vorname": kunde.vorname,
        "Name": kunde.name,
        "Geburtsdatum": kunde.geburtsdatum,
        "Geburtsort": kunde.geburtsort,
        "Staatsangehoerigkeit": kunde.staatsangehoerigkeit,
        "Vorwahl": kunde.vorwahl,
        "Telefonnummer": kunde.telefonnummer,
        "Email": kunde.email,
        "Familienstand": kunde.familienstand,
        "Strasse": kunde.adresse_obj.strasse,
        "Hausnummer": kunde.adresse_obj.hausnummer,
        "HausnummerZusatz": kunde.adresse_obj.hausnummerZusatz,
        "PLZ": kunde.adresse_obj.plz,
        "Ort": kunde.adresse_obj.ort,
    }

    reader = PdfReader(doc_file)
    # field_mapping = get_field_mapping(stammdaten.keys(), reader.get_fields().keys())
    field_mapping = {
        "Name": "Name",
        "Strasse_Hausnummer": "Strasse",
        "PLZ_Ort": "PLZ",
        "Telefonnummer": "Telefonnummer",
        "IBAN": None,
        "Vertragsname": None,
        "Zahlungsart": None,
        "BIC": None,
        "Ort": "Ort",
        "Referenznummer_Vertrag": None,
        "Adressfeld": None,
        "Datum_S1": None,
        "Datum_S2": None,
    }
    field_mapping = {k: v for k, v in field_mapping.items() if v is not None}
    data = {k: stammdaten[v] for k, v in field_mapping.items()}

    # fill pdf
    writer = PdfWriter()
    writer.append(reader)
    writer.set_need_appearances_writer()

    for page in writer.pages:
        writer.update_page_form_field_values(page, data, auto_regenerate=False)

    bio = io.BytesIO()
    writer.write(bio)
    filled_pdf = bio.getvalue()
    return Response(filled_pdf, media_type="application/pdf")


@app.get("/pdf/")
async def download_pdf(filename: str):
    # Define the directory where the files are stored
    directory = "./_Dokumentendump_"

    # Construct the full file path
    file_path = os.path.join(directory, filename)

    # Check if the file exists
    if not os.path.isfile(file_path):
        # If the file does not exist, raise an HTTP 404 Not Found exception
        raise HTTPException(status_code=404, detail="File not found")

    # Check if the file has a .pdf extension
    if not file_path.lower().endswith(".pdf"):
        # If the file is not a PDF, raise an HTTP 400 Bad Request exception
        raise HTTPException(status_code=400, detail="File is not a PDF")

    # If the file exists and is a PDF, return it as a FileResponse for downloading
    return FileResponse(file_path, media_type="application/pdf", filename=filename)



@app.get("/chat/")
async def chat(query: str, id: int, nutzer_db=Depends(get_nutzer_db)):
    user = nutzer_db.query(nutzer_models.Person).get(id)

    if not user:
        raise HTTPException(404, {"error": "User not found"})

    user_info = user.to_dict()

    ### Contextualize question ###
    contextualize_q_system_prompt = (
        "Given a chat history and the latest user question "
        "which might reference context in the chat history, "
        "formulate a standalone question which can be understood "
        "without the chat history. Do NOT answer the question, "
        "just reformulate it if needed and otherwise return it as is."
    )

    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", contextualize_q_system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    history_aware_retriever = create_history_aware_retriever(
        app.state.llm,
        app.state.vectorstore.get_store().as_retriever(),
        contextualize_q_prompt,
    )

    ### Answer question ###
    system_prompt = (
        "You are an assistant for question-answering tasks. "
        "Use the following user information and pieces of retrieved context to answer "
        "the question. If you don't know the answer, say that you "
        "don't know. Use three sentences maximum and keep the "
        "answer concise."
        "\n\n"
        "User information:\n"
        "{user_info}\n\n"
        "Context:\n"
        "{context}"
    )
    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(app.state.llm, qa_prompt)

    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    def get_session_history(session_id: str) -> BaseChatMessageHistory:
        if session_id not in app.state.store:
            app.state.store[session_id] = ChatMessageHistory()
        return app.state.store[session_id]

    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )

    response = conversational_rag_chain.invoke(
        {"input": query, "user_info": user_info},
        config={"configurable": {"session_id": str(id)}},
    )

    answer = response["answer"]

    # Extract source document names and calculate relative occurrence
    source_documents = response.get("context", [])
    document_counts = {}
    total_documents = len(source_documents)

    for document in source_documents:
        doc_name = document.metadata["source"]
        if doc_name in document_counts:
            document_counts[doc_name] += 1
        else:
            document_counts[doc_name] = 1

    # Calculate relative occurrence
    documents_with_relative_occurrence = [
        (doc_name, count / total_documents)
        for doc_name, count in document_counts.items()
    ]

    return {"answer": answer, "documents": documents_with_relative_occurrence}
