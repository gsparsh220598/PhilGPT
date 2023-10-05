from dotenv import load_dotenv
import os

load_dotenv()

from langchain.vectorstores import Chroma, Redis

from embeddings import get_embeddings

# refer this to fix port inaccessible error: https://stackoverflow.com/questions/11583562/how-to-kill-a-process-running-on-particular-port-in-linux
REDIS_URL = "redis://localhost:6379"
# REDIS_URL = "redis://localhost:6360"

VS_INDEX_NAME = "vectorstore"

emb_type = os.environ.get("EMB_TYPE")
embeddings = get_embeddings(emb_type)


def create_chroma_vector_store(text, persist_directory):
    print(f"Created New Chroma Vectorstore at {persist_directory}")
    print(f"Creating embeddings. May take some minutes...")
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    db.persist()
    keys = db.add_texts(text)
    return keys


def create_redis_vector_store(text, metadata):
    print(f"Creating embeddings. May take some minutes...")
    _, keys = Redis.from_texts_return_keys(
        texts=text,
        metadatas=metadata,
        redis_url=REDIS_URL,
        index_name=VS_INDEX_NAME,
        embedding=embeddings,
    )
    return keys


def load_redis_vector_store(index_name=VS_INDEX_NAME):
    print("Loading existing Redis Vectorstore")
    db = Redis.from_existing_index(
        redis_url=REDIS_URL,
        index_name=index_name,
        embedding=embeddings,
    )
    return db


def load_chroma_vector_store(persist_directory):
    print(f"Loading to existing Chroma Vectorstore at {persist_directory}")
    db = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )
    return db
