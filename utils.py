default_system_prompt = "A conversation between a user and an LLM-based AI assistant named Local Assistant. \
    Local Assistant gives helpful and honest answers."

PROMPT_TEMPLATE_FOR_GENERATION = """{system_prompt}
{user_prompt}
{assistant}
"""


def format_prompt(
    user_prompt: str,
    system_prompt: str = default_system_prompt,
) -> str:
    """
    Prompt template provided in https://huggingface.co/spaces/mosaicml/mpt-30b-chat/blob/main/app.py
    """

    formatted_prompt = PROMPT_TEMPLATE_FOR_GENERATION.format(
        system_prompt=f"<|im_start|>system\n{system_prompt}<|im_end|>\n",
        user_prompt=f"<|im_start|>user\n{user_prompt}<|im_end|>\n",
        assistant=f"<|im_start|>assistant\n\n",
    )
    return formatted_prompt


B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe. Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.

If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information."""


def get_llama_prompt(instruction, new_system_prompt=DEFAULT_SYSTEM_PROMPT):
    SYSTEM_PROMPT = B_SYS + new_system_prompt + E_SYS
    prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
    return prompt_template
