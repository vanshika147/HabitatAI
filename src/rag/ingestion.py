import time
from pathlib import Path
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "codebase_data"
DB_DIR = BASE_DIR / "chroma_db"

SUPPORTED_EXTENSIONS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".sql", ".sh", ".env.example"
}


def load_codebase_documents(data_dir: Path):
    """Recursively loads only supported source code and text documents."""
    docs = []
    for file_path in data_dir.rglob("*"):
        if (
            file_path.is_file()
            and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
            and ".git" not in file_path.parts
            and "__pycache__" not in file_path.parts
        ):
            try:
                loader = TextLoader(str(file_path), encoding="utf-8", autodetect_encoding=True)
                docs.extend(loader.load())
            except Exception as e:
                print(f"Skipping unreadable file {file_path.name}: {e}")
    return docs


def ingest_codebase(collection_name: str = "codebase"):
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{DATA_DIR}' created. Place code files inside.")
        return None

    raw_docs = load_codebase_documents(DATA_DIR)
    if not raw_docs:
        print(f"No supported code documents found in '{DATA_DIR}' to index.")
        return None

    print(f"Loaded {len(raw_docs)} source files. Splitting into chunks...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        separators=["\ndef ", "\nclass ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(raw_docs)
    print(f"Generated {len(chunks)} text chunks.")

    embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-001")

    vector_store = Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=str(DB_DIR),
    )

    BATCH_SIZE = 30
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        print(f"Embedding batch {i // BATCH_SIZE + 1} of {(len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE} ({len(batch)} chunks)...")
        vector_store.add_documents(batch)
        if i + BATCH_SIZE < len(chunks):
            time.sleep(15)

    print(f"Successfully ingested {len(chunks)} chunks into ChromaDB at '{DB_DIR}'.")
    return vector_store


if __name__ == "__main__":
    ingest_codebase()