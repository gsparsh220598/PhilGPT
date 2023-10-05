import glob
import os
from multiprocessing import Pool
from typing import List
import json
from pathlib import Path

import openai
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import (
    CSVLoader,
    PyMuPDFLoader,
    TextLoader,
    UnstructuredEmailLoader,
    UnstructuredEPubLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm

from embeddings import *
from vector_stores import (
    load_redis_vector_store,
    create_chroma_vector_store,
    create_redis_vector_store,
)

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
#  Load environment variables
persist_directory = os.environ.get("PERSIST_DIRECTORY")
# directory where source documents to be ingested are located
source_directory = os.environ.get("SOURCE_DIRECTORY", "source_documents")
embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
vs_type = os.environ.get("VS_TYPE")
chunk_size = 1000
chunk_overlap = 100
# MAX_CHUNKS_TO_INGEST = 900
oss = False
path_keys_json = "keys_metadata.json"

# Map file extensions to document loaders and their arguments
LOADER_MAPPING = {
    # ".csv": (CSVLoader, {}),
    ".docx": (UnstructuredWordDocumentLoader, {}),
    ".eml": (UnstructuredEmailLoader, {}),
    ".epub": (UnstructuredEPubLoader, {}),
    ".html": (UnstructuredHTMLLoader, {"encoding": "latin"}),
    ".md": (UnstructuredMarkdownLoader, {}),
    # ".odt": (UnstructuredODTLoader, {}),
    ".pdf": (PyMuPDFLoader, {}),
    ".pptx": (UnstructuredPowerPointLoader, {}),
    ".txt": (TextLoader, {}),
}


def load_single_document(file_path: str) -> List[Document]:
    ext = "." + file_path.rsplit(".", 1)[-1]
    if ext in LOADER_MAPPING:
        loader_class, loader_args = LOADER_MAPPING[ext]
        loader = loader_class(file_path, **loader_args)
        # print(f"Loading {file_path}")
        return loader.load()
    else:
        pass

    raise ValueError(f"Unsupported file extension '{ext}'")


def load_documents(source_dir: str) -> List[Document]:
    """
    Loads all documents from the source documents directory, ignoring specified files
    """
    p = Path(source_dir)
    all_files = []
    for ext in LOADER_MAPPING:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"**/*{ext}"), recursive=True)
        )
    print(f"Found {len(all_files)} files")
    print(f"Loading {len(all_files)} new documents")

    with Pool(processes=os.cpu_count()) as pool:
        results = []
        with tqdm(total=len(all_files), desc="Loading new documents", ncols=80) as pbar:
            for i, docs in enumerate(
                pool.imap_unordered(load_single_document, all_files)
            ):
                results.extend(docs)
                pbar.update()

    return results


def process_documents() -> List[Document]:
    """
    Load documents and split in chunks
    """
    print(f"Loading documents from {source_directory}")
    documents = load_documents(source_directory)
    # loader = DirectoryLoader(
    #     source_directory,
    #     use_multithreading=True,
    #     recursive=True,
    #     max_concurrency=os.cpu_count(),
    # )
    # documents = loader.load()
    print(f"Loaded {len(documents)} documents from {source_directory}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    texts = text_splitter.split_documents(documents)
    get_emb_cost_estimates(texts)
    print(f"Split into {len(texts)} chunks of text (max. {chunk_size} tokens each)")
    return texts


def does_vectorstore_exist(persist_directory: str, vs_type: str) -> bool:
    """
    Checks if vectorstore index exists
    """
    if vs_type == "redis":
        try:
            _ = load_redis_vector_store()
            return True
        except Exception as e:
            print(str(e))
            return False
    elif vs_type == "chroma":
        if os.path.exists(os.path.join(persist_directory, "index")):
            if os.path.exists(
                os.path.join(persist_directory, "chroma-collections.parquet")
            ) and os.path.exists(
                os.path.join(persist_directory, "chroma-embeddings.parquet")
            ):
                list_index_files = glob.glob(
                    os.path.join(persist_directory, "index/*.bin")
                )
                list_index_files += glob.glob(
                    os.path.join(persist_directory, "index/*.pkl")
                )
                # At least 3 documents are needed in a working vectorstore
                if len(list_index_files) > 3:
                    return True
        return False


def check_if_embeddings_exist(metadatas) -> bool:
    """
    1. open the keys_metadata.json file
    2. check if the metadata is in the keys_metadata.json file
    3. filter the metadata that is not in the keys_metadata.json file
    4. return the filtered metadata
    """
    print(f"Checking if embeddings already exists in {path_keys_json}...")
    unique_metadatas = set([m["source"] for m in metadatas])
    if os.path.exists(path_keys_json):
        with open(path_keys_json, "r") as f:
            if os.stat(path_keys_json).st_size == 0:
                return None
            keys_metadata = json.load(f)
        existing_metadata = [m for m in keys_metadata.values()]
        unq_existing_metadata = set(existing_metadata)
        filtered_metadata = list(unique_metadatas.difference(unq_existing_metadata))
        print(f"Found {len(filtered_metadata)} new documents to ingest")
        return
    else:
        return list(unique_metadatas)


def create_dict_from_keys(keys, metadata):
    """
    Create a dictionary from keys and metadata
    """
    with open(path_keys_json, "r+") as f:
        if os.stat(path_keys_json).st_size != 0:
            j = json.load(f)
            for i in range(len(keys)):
                j[keys[i]] = metadata[i]
            f.seek(0)
            json.dump(j, f, indent=4)
        else:
            j = {}
            for i in range(len(keys)):
                j[keys[i]] = metadata[i]
            json.dump(j, f, indent=4)


def process_docs_util():
    docs = process_documents()
    texts = [d.page_content for d in docs]
    metadatas = [d.metadata for d in docs]
    return texts, metadatas


def create_safe_embeddings():
    texts, metadata = process_docs_util()
    unq_filtered_metadata = check_if_embeddings_exist(metadata)
    filtered_texts = []
    filtered_metadatas = []
    if unq_filtered_metadata != None:
        for t, m in zip(texts, metadata):
            if metadata in unq_filtered_metadata:
                filtered_texts.append(t)
                filtered_metadatas.append(m)
        #     keys = db.add_texts(filtered_texts, filtered_metadatas)
        #     create_dict_from_keys(keys, filtered_metadatas)
        # else:
        #     keys = db.add_texts(texts, metadata)
        #     create_dict_from_keys(keys, metadata)
        print(f"Found {len(filtered_texts)} new docs to ingest")
        return filtered_texts, filtered_metadatas
    else:
        print("Found no docs in the keys_metadata.json file")
        return texts, metadata


def main():
    # vs_type = str(input("choose vectorstore type (chroma/redis): "))
    # db_exists = does_vectorstore_exist(persist_directory, vs_type)
    # # db_exists = False
    # if db_exists:
    #     if vs_type == "redis":
    #         db = load_redis_vector_store()
    #         create_safe_embeddings(db)

    #     elif vs_type == "chroma":
    #         db = load_chroma_vector_store(persist_directory)
    #         create_safe_embeddings(db)
    #     else:
    #         raise NotImplementedError()
    # else:
    texts, metadatas = create_safe_embeddings()
    proceed = input("Do you want to proceed with creating embeddings? (y/n): ")
    if proceed == "n":
        exit(0)
    if vs_type == "redis":
        keys = create_redis_vector_store(texts, metadatas)
        create_dict_from_keys(keys, metadatas)
    elif vs_type == "chroma":
        keys = create_chroma_vector_store(texts, persist_directory)
        create_dict_from_keys(keys, metadatas)
    else:
        raise NotImplementedError()

    print(f"Ingestion complete!")


if __name__ == "__main__":
    main()
