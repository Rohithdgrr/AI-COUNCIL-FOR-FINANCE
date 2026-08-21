from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_cohere import ChatCohere
import os


def get_groq_client(model="llama-3.3-70b-versatile", streaming=False):
    return ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name=model, temperature=0.3, max_tokens=2048, streaming=streaming)


def get_openrouter_client(model="meta-llama/llama-3.3-70b-instruct:free", streaming=False):
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048, streaming=streaming,
        default_headers={"HTTP-Referer": "https://supplychaingpt.ai", "X-Title": "SupplyChainGPT"},
    )


def get_nvidia_client(model="meta/llama-3.1-8b-instruct", streaming=False):
    return ChatOpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=os.getenv("NVIDIA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048, streaming=streaming,
    )


def get_google_client(model="gemini-flash-latest", streaming=False):
    return ChatGoogleGenerativeAI(google_api_key=os.getenv("GOOGLE_API_KEY"), model=model, temperature=0.3, streaming=streaming)


def get_cohere_client(model="command-r-plus", streaming=False):
    return ChatCohere(cohere_api_key=os.getenv("COHERE_API_KEY"), model=model, temperature=0.3, streaming=streaming)


def get_sambanova_client(model="Meta-Llama-3.3-70B-Instruct", streaming=False):
    return ChatOpenAI(
        base_url="https://api.sambanova.ai/v1",
        api_key=os.getenv("SAMBANOVA_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048, streaming=streaming,
    )


def get_mistral_client(model="mistral-large-latest", streaming=False):
    return ChatOpenAI(
        base_url="https://api.mistral.ai/v1",
        api_key=os.getenv("MISTRAL_API_KEY"),
        model=model, temperature=0.3, max_tokens=2048, streaming=streaming,
    )
