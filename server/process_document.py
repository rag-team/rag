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


for dir in ["_Dokumentendump_", "Archiv", "Conf", "Logs"]:
    os.makedirs(dir, exist_ok=True)

logger = splitOutErrLogger(
    "Logs/WSpeicher_Archiv.log",
    "Logs/WSpeicher_Error.log",
    name=__name__,
    level=logging.WARNING,
)
loopback_logger = fileLogger("Logs/loopback.log", name="loopback", format="%(message)s")


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
    reader = PdfReader(os.path.join("_Dokumentendump_", filename))
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
    with open(os.path.join("_Dokumentendump_", filename), "wb") as f:
        writer.write(f)
    logger.info(f"Added metadata for {filename} to {filename}")

    # Add to vector store
    logger.debug(f"Ingesting {filename} into vector store")
    vectorstore.injest_files(files=[os.path.join("_Dokumentendump_", filename)])
    logger.info(f"Ingested {filename} into vector store")

    # Decide how to process the document based on if it has form fields
    fields = reader.get_fields()
    logging.debug(f"Found {len(fields)} fields in {filename}")

    if fields:
        return process_form(filename, timestamp, session)
    else:
        return process_noform(filename, timestamp, session)


def process_form(filename, timestamp, session):
    logging.info("Processing document with form fields {filename}")

    reader = PdfReader(filename)
    fields = reader.get_fields()

    # Go through all fields and process them individually
    error = False
    for name, field in fields.items():
        logging.debug(f"Processing field {name} of type {field.field_type}")

        # Check if Schlagwort exists in database
        schlagwort = session.execute(
            select(models.Schlagwort).where(models.Schlagwort.schlagwort == name)
        ).scalar()

        # If not, check if synonym exists in database
        if not schlagwort:
            logger.debug(f"Schlagwort {name} not found in database. Checking synonyms")
            synonym = session.execute(
                select(models.Synonym).where(models.Synonym.synonym == name)
            ).scalar()
            if not synonym:
                logger.error(f"No synonym for Schlagwort {name} found in database.")
                loopback_logger.info(
                    "%s\t%s\t%s\t%s", timestamp, filename, 1, "Schlagwort not found"
                )
                error = True
                continue

            schlagwort = synonym.schlagwort_obj.schlagwort

        # Add field to database
        logging.info(f"Found Schlagwort {schlagwort} in database")
        feld = models.Feld(
            schlagword=schlagwort.pkey, feldname=name, feldtyp=field.field_type
        )
        session.add(feld)
        session.commit()
        logging.debug(f"Added field {name} to Felder table")

        # Move document to Archiv
        os.rename(
            os.path.join("_Dokumentendump_", filename), os.path.join("Archiv", filename)
        )
        logging.info("Moved {filename} to Archiv")

    return "ERROR" if error else "SUCCESS"


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
