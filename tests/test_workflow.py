import truststore
truststore.inject_into_ssl()

import asyncio
from dotenv import load_dotenv
from src.graph.workflow import create_sdlc_graph, _get_text_content

load_dotenv()


async def main():
    print("Compiling HabitatAI Multi-Agent SDLC Graph...")
    graph = await create_sdlc_graph()

    test_queries = [
        ("Support Test", "Check the repository health and inspect the local working directory."),
        ("Refactor Test", "Analyze run.py and identify any tech debt or missing type hints."),
    ]

    for label, query in test_queries:
        print(f"\n==================== {label} ====================")
        print(f"User Query: {query}")
        
        response = await graph.ainvoke({
            "messages": [("user", query)]
        })
        
        print(f"Executed Agent Node: {response.get('next_agent')}")
        print("\n--- Agent Response ---")
        print(_get_text_content(response["messages"][-1]))


if __name__ == "__main__":
    asyncio.run(main())