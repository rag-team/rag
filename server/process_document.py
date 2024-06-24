import argparse
import getpass
import logging
import os
import traceback
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from sqlalchemy import select

from server.loggers import fileLogger, splitOutErrLogger
from server.schlagwortdb import models
from server.schlagwortdb.database import SessionLocal, engine
from server.vectordb import VectorStore

TIME_FORMAT = "%Y-%m-%d-%H-%M-%S"

logger = splitOutErrLogger(
    "/server_data/Logs/WSpeicher_Archiv.log",
    "/server_data/Logs/WSpeicher_Error.log",
    name=__name__,
    level=logging.INFO,
)
loopback_logger = fileLogger("/server_data/Logs/loopback.log", name="loopback", format="%(message)s")


def process_document(filename, session, vectorstore):
    if not filename.endswith(".pdf"):
        logger.error("Only PDF files are supported. Aborting...")
        return "ERROR"

    logger.info(f"Processing document {filename}")

    # Created ID from original name and time stamp
    filename_wo_pdf = filename.rsplit(".")[0]
    timestamp = datetime.now().strftime(TIME_FORMAT)
    file_id = f"{filename_wo_pdf}_{timestamp}"
    logger.debug(f"File ID: {file_id}")

    # Get user who started the processing
    user = getpass.getuser()
    logger.debug(f"User: {user}")

    # Add metadata to the document
    reader = PdfReader(os.path.join("/", "server_data", "_Dokumentendump_", filename))
    writer = PdfWriter()
    writer.append(reader)
    writer.set_need_appearances_writer()
    writer.add_metadata(
        {
            **reader.metadata,
            "/FileID": file_id,
            "/ProcessedAt": timestamp,
            "/OriginalFileName": filename,
            "/UserWhoStartedProcessing": user,
        }
    )

    logger.debug(f"Writing document with added metadata to {filename}")
    with open(os.path.join("/", "server_data", "_Dokumentendump_", filename), "wb") as f:
        writer.write(f)
    logger.info(f"Added metadata for {filename} to {filename}")

    # Add to vector store
    logger.debug(f"Ingesting {filename} into vector store")
    vectorstore.injest_files(files=[os.path.join("/", "server_data", "_Dokumentendump_", filename)])
    logger.info(f"Ingested {filename} into vector store")

    # Decide how to process the document based on if it has form fields
    fields = reader.get_fields()
    logger.debug(f"Found {len(fields)} fields in {filename}")

    if fields:
        return process_form(filename, timestamp, session)
    else:
        return process_noform(filename, timestamp, session)


def process_form(filename, timestamp, session):
    logger.info(f"Processing document with form fields {filename}")

    reader = PdfReader(os.path.join("/", "server_data", "_Dokumentendump_", filename))
    fields = reader.get_fields()

    file_id = reader.metadata["/FileID"]
    doc = models.DokumentLookup(docName=file_id, docOrigName=filename)
    session.add(doc)
    session.flush()
    logger.debug(f"Added document '{file_id}' to DokumentLookup table (not commited)")

    # Go through all fields and process them individually
    error = False
    for name, field in fields.items():
        logger.debug(f"Processing field '{name}' of type {field.field_type}")

        # Check if Schlagwort exists in database
        schlagwort = session.execute(
            select(models.Schlagwort).where(models.Schlagwort.schlagwort == name)
        ).scalar()

        # If not, check if synonym exists in database
        if not schlagwort:
            # Add schlagwort to DB
            schlagwort = models.Schlagwort(schlagwort=name)
            session.add(schlagwort)
            session.flush()
            logger.debug(f"Added Schlgwrt '{name}' to Schlagworte table (not commited)")

            # logger.debug(
            #     f"Schlagwort '{name}' not found in database. Checking synonyms"
            # )
            # synonym = session.execute(
            #     select(models.Synonym).where(models.Synonym.synonym == name)
            # ).scalar()
            # if not synonym:
            #     logger.error(f"No synonym for Schlagwort '{name}' found in database.")
            #     loopback_logger.info(
            #         "%s\t%s\t%s\t%s", timestamp, filename, 1, "Schlagwort not found"
            #     )
            #     error = True
            #     continue

            # schlagwort = synonym.schlagwort_obj.schlagwort

        # Add field to database
        logger.info(f"Found Schlagwort '{schlagwort}' in database")

        # TODO: should normally (according to Liss) be added unconditionally
        # Not sure how that would work out though...
        feld = session.execute(
            select(models.Feld)
            .where(models.Feld.feldname == name)
        ).scalar()
        if not feld:
            feld = models.Feld(
                schlagwort=schlagwort.pkey, feldname=name, feldtyp=field.field_type
            )
            session.add(feld)
            logger.debug(f"Added field '{name}' to Felder table (not commited)")

        # Add field to schlagwort_dokument
        session.add(
            models.SchlagwortDokument(schlagwort=schlagwort.pkey, dokument=doc.pkey)
        )
        logger.debug(f"Added field '{name}' to SchlagwortDokument table (not commited)")

    if not error:
        logger.debug(f"No errors occurred. Committing session and moving to Archiv...")
        session.commit()
        logger.debug(f"Commited session")

        # Move document to Archiv
        os.rename(
            os.path.join("/", "server_data", "_Dokumentendump_", filename), 
            os.path.join("/", "server_data", "Archiv", file_id)
        )
        logger.debug(f"Moved {filename} to Archiv/{file_id}")

        logger.info(f"Succesfully processed document {filename}")
        return "SUCCESS"

    logger.error(f"Errors occurred. Rolling back session...")
    session.rollback()
    logger.debug(f"Rolled back session")
    return "ERROR"


def process_noform(*args):
    logger.warning("I don't know how to process documents without form fields yet")
    return "ERROR"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a document")
    parser.add_argument("document", type=str, help="The document to process")

    try:
        args = parser.parse_args()
        models.Base.metadata.create_all(bind=engine)
        session = SessionLocal()
        vectorstore = VectorStore()
        status = process_document(args.document, session, vectorstore)
        print(status)
    except Exception as e:
        logger.critical(f"An error occurred: {e}. Traceback:\n{traceback.format_exc()}")
        print("ERROR_FATAL")
