from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.tools import create_retriever_tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings

BASE_DIR = Path(__file__).resolve().parents[2]
DB_DIR = BASE_DIR / "chroma_db"


def get_codebase_retriever_tool(collection_name: str = "codebase"):
    """Returns a LangChain retriever tool bound to local ChromaDB using Gemini embeddings."""
    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

    vector_store = Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    retriever = vector_store.as_retriever(
        search_type="similarity", search_kwargs={"k": 4}
    )

    return create_retriever_tool(
        retriever,
        name="search_codebase_knowledge",
        description="Searches indexed repository code, API specs, and project docs.",
    )