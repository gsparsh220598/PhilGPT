from langchain.embeddings import HuggingFaceEmbeddings, OpenAIEmbeddings
import os
import openai

embeddings_model_name = os.environ.get("EMBEDDINGS_MODEL_NAME")
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_embeddings(emb_type):
    """
    function to initialize embeddings
    """
    if emb_type == "hf":
        embeddings = HuggingFaceEmbeddings(model_name=embeddings_model_name)
    elif emb_type == "openai":
        embeddings = OpenAIEmbeddings()
    else:
        raise ValueError("Embedding type not supported")
    return embeddings


def get_emb_cost_estimates(docs):
    total_characters = 0
    for doc in docs:
        total_characters += len(doc.page_content)

    total_tokens = total_characters / 4
    emb_cost = total_tokens * 0.0001 / 1000  # 0.0001 USD per 1000 tokens

    print("Total number of characters:", total_characters)
    print("Total number of tokens:", total_tokens)
    print("Cost of creating embeddings:", emb_cost)
