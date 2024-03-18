import os
import time

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings

start = time.time()

PATH = "./data"
loader = PyPDFDirectoryLoader(PATH)
docs = loader.load()
print("Loaded", len(docs), "documents")

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000, chunk_overlap=200, add_start_index=True
)
all_splits = text_splitter.split_documents(docs)


end = time.time()
print("Time taken to split documents:", end - start, "seconds")
start = time.time()




model_name = "BAAI/bge-small-en-v1.5"
model_kwargs = {'device': 'cuda'}
encode_kwargs = {'normalize_embeddings': False}
embedding_model = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

store = PGVector(
    collection_name=COLLECTION_NAME,
    connection_string=CONNECTION_STRING,
    embedding_function=embedding_model,
    pre_delete_collection=True,
)

end = time.time()
print("Time taken to load model:", end - start, "seconds")


start = time.time()
store.add_documents(all_splits, verbose=True)
end = time.time()
print("Time taken to add documents:", end - start, "seconds")