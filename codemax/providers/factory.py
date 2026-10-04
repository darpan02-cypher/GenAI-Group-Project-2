"""Pick a provider by name, using settings from environment variables / .env."""
import os

from dotenv import load_dotenv

from .base import LangChainProvider, LLMProvider


def make_provider(name: str | None = None) -> LLMProvider:
    load_dotenv()
    name = (name or os.getenv("CODEMAX_PROVIDER", "groq")).lower()

    if name == "groq":
        from langchain_groq import ChatGroq

        if not os.getenv("GROQ_API_KEY"):
            raise RuntimeError("GROQ_API_KEY is not set (put it in .env)")
        model = ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=0,
        )
        provider = LangChainProvider(model)
    elif name == "ollama":
        from langchain_ollama import ChatOllama

        model = ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
        )
        provider = LangChainProvider(model)
    else:
        raise ValueError(f"Unknown provider '{name}'. Use 'groq' or 'ollama'.")

    provider.name = name
    return provider
