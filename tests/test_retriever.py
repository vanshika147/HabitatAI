from dotenv import load_dotenv
from src.rag.retriever import get_codebase_retriever_tool

load_dotenv()


def main():
    print("Testing Codebase Retriever Tool...")
    tool = get_codebase_retriever_tool()

    query = "HabitatAI operational"
    print(f"Running query: '{query}'\n")

    result = tool.invoke(query)
    print("--- Retriever Output ---")
    print(result)


if __name__ == "__main__":
    main()