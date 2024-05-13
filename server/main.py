import io
import json
import os

from fastapi import FastAPI, File, Response, UploadFile
from langchain_community.llms.llamacpp import LlamaCpp
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pypdf import PdfReader, PdfWriter

app = FastAPI()

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

    # prompt = ChatPromptTemplate.from_template(PROMPT)
    # model = LlamaCpp(
    #     model_path="models/open-llama-3b-v2-wizard-evol-instuct-v2-196k.Q4_K_M.gguf",
    #     temperature=0.5,
    #     verbose=True,
    #     n_ctx=2048,
    #     n_batch=256,
    #     n_gpu_layers=-1,
    # )
    # from langchain_anthropic import ChatAnthropic
    # model = ChatAnthropic(model="claude-3-opus-20240229")

    # output = StrOutputParser()
    # chain = prompt | model | output

    # result = chain.invoke(
    #     {
    #         "fields": {name: field.field_type for name, field in fields.items()},
    #         "context": json.dumps(context),
    #     }
    # )

    # This is what claude gave me.
    result = r"""{"Name des Betreuers": "Dr. Hans Mustermann", "Adresse des Betreuers": null, "Titel der Lab Rotation": null, "BCCNBetreuer für externe Lab Rotations": null, "Angestrebter Zeitraum": "01.01.2023 - 31.12.2023", "Titel der Lab Rotation_2": "Erlernen von Python", "Ort  location": null, "Datum  date": null, "Check Box1": null, "Check Box3": null, "Check Box4": null, "Check Box5": null, "Check Box7": null, "Check Box8": null, "Matrikelnummer": null, "Name des Studierenden": "Herbert Basti"}"""

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
