import os
from typing import Optional, Union
import instructor
from instructor import Mode, Instructor, AsyncInstructor

# Import all necessary clients and Instructor wrappers
from openai import OpenAI, AsyncOpenAI
from anthropic import Anthropic, AsyncAnthropic
import cohere
from groq import Groq, AsyncGroq
from mistralai.client import MistralClient
from mistralai.async_client import MistralAsyncClient


from any_llm import model_mapping, Provider


def get_default_mode(provider: Provider) -> Mode:
    """
    Fetches default instructor mode for a given model provider
    """
    org_to_mode = {
        Provider.OPENAI: Mode.TOOLS,
        Provider.ANTHROPIC: Mode.ANTHROPIC_TOOLS,
        Provider.COHERE: Mode.COHERE_TOOLS,
        Provider.GROQ: Mode.TOOLS,
        Provider.MISTRAL: Mode.MISTRAL_TOOLS,
        Provider.ANYSCALE: Mode.JSON_SCHEMA,
    }
    assert provider in org_to_mode, f"Provider '{provider.value}' is not recognized."
    return org_to_mode[provider]


def get_api_key(provider: Provider):
    """
    Fetches the API key for a given model provider
    """
    model_to_api_key = {
        Provider.OPENAI: os.getenv("OPENAI_API_KEY"),
        Provider.ANTHROPIC: os.getenv("ANTHROPIC_API_KEY"),
        Provider.ANYSCALE: os.getenv("ANYSCALE_API_KEY"),
        Provider.COHERE: os.getenv("COHERE_API_KEY"),
        Provider.VOYAGE: os.getenv("VOYAGE_API_KEY"),
        Provider.GROQ: os.getenv("GROQ_API_KEY"),
        Provider.MISTRAL: os.getenv("MISTRAL_API_KEY"),
    }
    assert (
        provider in model_to_api_key
    ), f"Provider '{provider}' is not recognized."
    return model_to_api_key[provider]


# TODO: gemini, together, ollama, llamacpp
def from_any(
    provider: Provider,
    model_name: str,
    async_client: bool = False,
    mode: Optional[Mode] = None,
) -> Union[Instructor, AsyncInstructor]:
    """
    Factory function to get the appropriate Instructor-wrapped client for a given model.

    Args:
        model_name (str): The name of the model to use.
        async_client (bool): Whether to return async clients. Defaults to False.
        mode (Optional[Mode]): The Mode to use for the Instructor client. If None, uses the default for the organization.

    Returns:
        Union[Instructor, AsyncInstructor]: The Instructor-wrapped client.
    """
    api_key = get_api_key(provider)

    if mode is None:
        mode = get_default_mode(provider)

    if provider == Provider.OPENAI:
        raw_client = AsyncOpenAI() if async_client else OpenAI()
        return instructor.from_openai(raw_client, mode=mode)
    elif provider == Provider.ANTHROPIC:
        raw_client = AsyncAnthropic() if async_client else Anthropic()
        return instructor.from_anthropic(raw_client, mode=mode)
    elif provider == Provider.COHERE:
        raw_client = cohere.AsyncClient() if async_client else cohere.Client()
        return instructor.from_cohere(
            raw_client, max_tokens=0, model=model_name, mode=mode
        )
    elif provider == Provider.GROQ:
        raw_client = AsyncGroq(api_key=api_key) if async_client else Groq(api_key=api_key)
        return instructor.from_groq(raw_client, mode=mode)
    elif provider == Provider.MISTRAL:
        raw_client = MistralAsyncClient() if async_client else MistralClient()
        return instructor.from_openai(create=raw_client.chat, mode=mode)
    elif provider == Provider.ANYSCALE:
        raw_client = AsyncOpenAI(
            base_url="https://api.endpoints.anyscale.com/v1",
            api_key=api_key,
        ) if async_client else OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1",
            api_key=api_key,
        )
        return instructor.from_openai(raw_client, mode=mode)
    else:
        raise ValueError(f"Cannot create client for unsupported provider: {provider}")


def get_chat_urls(model_name: str) -> str:
    """
    Retrieves the chat URL for a given organization, model name, and workload.
    """
    org = model_mapping[model_name].org
    model_to_chat_url = {
        "openai": "https://api.openai.com/v1/chat/completions",
        "anyscale": "https://api.endpoints.anyscale.com/v1/chat/completions",
        "anthropic": "https://api.anthropic.com/v1/messages",
        "cohere": "https://api.cohere.ai/v1/chat/completions",
        "voyage": "https://api.voyageai.com/v1/embeddings",
    }
    return model_to_chat_url[org]
