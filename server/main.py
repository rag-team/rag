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
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain.memory.buffer import ConversationBufferMemory
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pypdf import PdfReader, PdfWriter

from server.loggers import splitOutErrLogger
from server.schlagwortdb import models
from server.schlagwortdb.database import SessionLocal, engine
from server.vectordb import VectorStore

MODEL_PATH = os.path.join(
    os.path.dirname(__file__),
    #"models/tinyllama-1.1b-chat-v0.3.Q4_K_M.gguf"
    "models/llama-2-13b-chat.Q5_K_M.gguf"
    #"models/leo-mistral-hessianai-7b-chat.Q5_K_M.gguf"
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


# models.Base.metadata.drop_all(bind=engine)
models.Base.metadata.create_all(bind=engine)
app = FastAPI(lifespan=lifespan)
app.state.previous_id = None
app.state.memories = {}

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
            ("system", """
             You are a helpful assistant who matches inputs to keywords. A user will
             give you a list of inputs, and you have to respond which keywords the
             inputs belong to. If an input doesn't belong to any keyword, respond with
             `None`. Important: always respond in JSON format.
             Here is a list of keywords: {keywords}
             """),
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


@app.get("/chat/")
async def chat(query: str, id: int, db=Depends(get_db)):

    user = db.query(models.Kunde).get(id)
    if not user:
        return {"error": "User not found"}

    logger.debug(f"Found user fields in pkey={user.pkey}, name={user.name}")

    # Check if this is the first request or if the id has changed
    if app.state.previous_id is None or app.state.previous_id != id:
        # Extract user information
        user_info = f"""
            Nutzerinformation:
            Name: {user.vorname} {user.name}
            Anrede: {user.anrede}
            Geburtsdatum: {user.geburtsdatum}
            Geburtsort: {user.geburtsort}
            Staatsangehörigkeit: {user.staatsangehoerigkeit}
            Vorwahl: {user.vorwahl}
            Telefonnummer: {user.telefonnummer}
            Email: {user.email}
            Familienstand: {user.familienstand}
            Adresse:
                Straße: {user.adresse_obj.strasse} {user.adresse_obj.hausnummer}{user.adresse_obj.hausnummerZusatz}
                PLZ: {user.adresse_obj.plz}
                Ort: {user.adresse_obj.ort}
            """

        # Update the previous_id in app.state
        app.state.previous_id = id
        query = f"Alle folgenden Antworten sollen auf den Nutzer mit den folgenden Parametern abgestimmt sein {user_info}\n\n Query: {query}"

        # Check if there is an existing memory for this user id
    if id not in app.state.memories:
        app.state.memories[id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"  # Specify the key to store in memory
        )

    memory = app.state.memories[id]

    chain = ConversationalRetrievalChain.from_llm(
        llm=app.state.llm,
        retriever=app.state.vectorstore.get_store().as_retriever(search_k=5),
        memory=memory,
        return_source_documents=True,
    )
    response = chain(query)

    # Extract the source documents
    source_documents = response.get("source_documents", [])

    # Extract document names and similarity scores
    doc_info = [(doc.metadata["name"], doc.metadata["score"]) for doc in source_documents]

    # Print out the source documents
    for doc in source_documents:
        print("Documents", doc)

    # Return both answer and source documents info
    return {
        "answer": response["answer"],
        "source_documents_info": doc_info
    }

