import truststore
truststore.inject_into_ssl()

import asyncio
from dotenv import load_dotenv
from src.agents.refactor import build_refactor_agent

load_dotenv()


async def main():
    print("Testing HabitatAI Refactor Agent...")
    refactor_agent = await build_refactor_agent()

    test_prompt = (
        "Inspect 'run.py' in the repository root. Check if it lacks type annotations "
        "or docstrings, and describe what refactoring steps would modernize it."
    )

    response = await refactor_agent.ainvoke({"messages": [("user", test_prompt)]})

    last_message = response["messages"][-1]
    if isinstance(last_message.content, list):
        final_text = "".join(
            block.get("text", "")
            for block in last_message.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        final_text = last_message.content

    print("\n--- Refactor Agent Analysis ---")
    print(final_text)


if __name__ == "__main__":
    asyncio.run(main())