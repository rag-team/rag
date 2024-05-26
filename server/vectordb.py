import os

import pypdfium2 as pdfium
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain_text_splitters import RecursiveCharacterTextSplitter


class VectorStore():
    COLLECTION_NAME = "test_collection"
    CONNECTION_STRING = PGVector.connection_string_from_db_params(
        driver=os.environ.get("PGVECTOR_DRIVER", "psycopg2"),
        host=os.environ.get("PGVECTOR_HOST", "localhost"),
        port=int(os.environ.get("PGVECTOR_PORT", "5432")),
        database=os.environ.get("PGVECTOR_DATABASE", "vectordb"),
        user=os.environ.get("PGVECTOR_USER", "postgres"),
        password=os.environ.get("PGVECTOR_PASSWORD", "password"),
    )

    model_name = "BAAI/bge-small-en-v1.5"
    model_kwargs = {'device': 'cuda'}
    encode_kwargs = {'normalize_embeddings': False}

    def __init__(self):
        # chek if on mac or windows
        if os.name == 'posix':
            self.model_kwargs = {'device': 'cpu'}

        self.embedding_model = HuggingFaceEmbeddings(
            model_name=self.model_name,
            model_kwargs=self.model_kwargs,
            encode_kwargs=self.encode_kwargs
        )

        self.store = PGVector(
            collection_name=self.COLLECTION_NAME,
            connection_string=self.CONNECTION_STRING,
            embedding_function=self.embedding_model,
            pre_delete_collection=True,
        )

    def get_store(self):
        return self.store

    def injest_files(self, files):
        pdf_text = self.get_pdf_text(files)
        text_chunks = self.get_text_chunks(pdf_text)
        self.store.add_texts(text_chunks)

    def get_text_chunks(self, text):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=50)
        chunks = text_splitter.split_text(text)
        return chunks

    def get_pdf_text(self, pdf_docs):
        text = ""
        for pdf in pdf_docs:
            pdf_reader = pdfium.PdfDocument(pdf)
            for i in range(len(pdf_reader)):
                page = pdf_reader.get_page(i)
                textpage = page.get_textpage()
                text += textpage.get_text_bounded() + "\n"
        return text
