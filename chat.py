from dataclasses import asdict, dataclass
import os
import time

from dotenv import load_dotenv
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.llms import CTransformers
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
import openai

from constants import CHAT_MODEL, CHAT_PROMPT, CHAT_PROMPT_LLAMA
from memory import load_chat_history

from utils import *

# from cache import *

# from question_answer_docs import load_model

load_dotenv()

model_path = os.environ.get("MODEL_PATH")
openai.api_key = os.environ.get("OPENAI_API_KEY")
emb_type = os.environ.get("EMB_TYPE")
vs_type = os.environ.get("VS_TYPE")


@dataclass
class GenerationConfig:
    # sample
    top_k: int
    top_p: float
    temperature: float
    repetition_penalty: float
    gpu_layers: int
    # last_n_tokens: int
    seed: int

    # eval
    # batch_size: int
    # threads: Optional[int]

    # generate
    max_new_tokens: int
    # stop: list[str]
    stream: bool
    # reset: bool


generation_config = GenerationConfig(
    temperature=0.1,
    top_k=0,
    top_p=0.9,
    repetition_penalty=1.2,
    max_new_tokens=1024,
    gpu_layers=1000,
    seed=42,
    # reset=False,
    stream=True,  # streaming per word/token
    # threads=int(os.cpu_count() / 2),  # adjust for your CPU
    # stop=["<|im_end|>", "|<"],
    # last_n_tokens=64,
    # batch_size=8,
)


def get_conv_chain(vs_type="redis", emb_type="hf"):
    # load the memory from a json file
    retrieved_memory = load_chat_history(qa=False, vs_type=vs_type)
    if emb_type == "openai":
        return ConversationChain(llm=llm, memory=retrieved_memory, prompt=CHAT_PROMPT)
    else:
        return ConversationChain(
            llm=llm, memory=retrieved_memory, prompt=CHAT_PROMPT_LLAMA
        )


def load_model(emb_type):
    try:
        # check if the model is already downloaded
        print("Loading model...")
        global llm, cond_llm
        # initialize llm
        emb_type = bool(emb_type == "hf")
        if emb_type:
            llm = CTransformers(
                model="TheBloke/Llama-2-7B-Chat-GGML",
                model_file=os.path.abspath(model_path),
                callbacks=[StreamingStdOutCallbackHandler()],
                config=asdict(generation_config),
            )
        else:
            llm = ChatOpenAI(
                model_name=CHAT_MODEL,
                temperature=0.1,
                streaming=True,
                callbacks=[StreamingStdOutCallbackHandler()],
            )
            # cond_llm = OpenAI(model=COND_MODEL, temperature=0.1)
        return True

    except Exception as e:
        print(str(e))
        raise


if __name__ == "__main__":
    # load model if it has already been downloaded. If not prompt the user to download it.
    load_model(emb_type)
    chain = get_conv_chain(vs_type, emb_type)

    while True:
        query = input("\nEnter a question: ")
        if query == "exit":
            break
        if query.strip() == "":
            continue
        try:
            print("Thinking...")
            # call llm with formatted user prompt and generation config
            start = time.time()
            response = chain({"input": query})
            # response = llm(get_llama_prompt(query), **asdict(generation_config))
            end = time.time()
            # print response
            print(f"\n> Answer (took {round(end - start, 2)} s.):")
            print("\n")
        except Exception as e:
            print(str(e))
            raise
