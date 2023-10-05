from langchain.memory import (
    RedisChatMessageHistory,
    ChatMessageHistory,
    ConversationBufferMemory,
)
from langchain.schema.messages import messages_from_dict, messages_to_dict
from datetime import datetime
import json
import os
from typing import Any, Dict

from constants import *
from vector_stores import REDIS_URL

MEM_INDEX_NAME = "chat_history"


# TODO: cite where the soln has been taken from
class AnswerConversationBufferMemory(ConversationBufferMemory):
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        return super(AnswerConversationBufferMemory, self).save_context(
            inputs, {"response": outputs["answer"]}
        )


def retrieve_chat_history(chat_len=0):
    try:
        with open("chat_history.json", "r") as f:
            if os.stat("chat_history.json").st_size == 0:
                retrieve_from_db = []
            else:
                retrieve_from_db = json.load(f)
            # use only last 15 messages
        retrieve_from_db = retrieve_from_db[-1 * chat_len :]
    except FileNotFoundError:
        retrieve_from_db = []
    retrieved_messages = messages_from_dict(retrieve_from_db)
    return retrieved_messages


def load_chat_history(qa=True, vs_type="redis"):
    """
    Load the memory from a json file.
    taken from: https://stackoverflow.com/questions/75965605/how-to-persist-langchain-conversation-memory-save-and-load
    """
    if vs_type == "redis":
        try:
            retrieved_chat_history = RedisChatMessageHistory(
                session_id=f"{MEM_INDEX_NAME}:",
                url=REDIS_URL,
            )
        except:
            retrieved_chat_history = ChatMessageHistory(messages=[])
    else:
        retrieved_messages = retrieve_chat_history(CHAT_HISTORY_LEN)
        retrieved_chat_history = ChatMessageHistory(
            messages=retrieved_messages
        )  # TODO: change this to get redis chat history
    if qa:
        retrieved_memory = AnswerConversationBufferMemory(
            chat_memory=retrieved_chat_history,
            memory_key="chat_history",
            return_messages=True,
        )
    else:
        retrieved_memory = ConversationBufferMemory(
            chat_memory=retrieved_chat_history,
            memory_key="history",
            # input_key="question",
            return_messages=True,
        )
    return retrieved_memory


def save_chat_history(chain, vs_type="redis"):
    """
    Load the memory from a json file.
    taken from: https://stackoverflow.com/questions/75965605/how-to-persist-langchain-conversation-memory-save-and-load
    """
    if vs_type != "redis":
        extracted_msgs = chain.memory.chat_memory.messages
        ingest_to_db = messages_to_dict(extracted_msgs)
        # safely append to the chat_history.json file
        with open("chat_history.json", "w") as f:
            json.dump(ingest_to_db, f)
    else:
        print("Saving chat history to redis")
