import truststore
truststore.inject_into_ssl()

import asyncio
from dotenv import load_dotenv
from src.agents.developer import build_developer_agent

load_dotenv()


async def main():
    print("Testing HabitatAI Developer Agent (Persistent 'habitat-dev' Branch Flow)...")
    developer_agent = await build_developer_agent()

    test_prompt = (
        "Perform the following task on 'test-habitatai/PurePill-habitatAI':\n"
        "1. Create or update the file 'docs/ARCHITECTURE.md' on the dedicated working branch 'habitat-dev' "
        "with a short markdown document explaining the role of the Developer, Support, and Refactor agents.\n"
        "2. Ensure a Pull Request is active from 'habitat-dev' targeting 'main' with title 'feat: Agent Architecture Documentation'. "
        "If a PR already exists, confirm that the changes were appended to the existing PR."
    )

    response = await developer_agent.ainvoke({
        "messages": [("user", test_prompt)]
    })

    # Clean display handling for Gemini output blocks
    last_message = response["messages"][-1]
    if isinstance(last_message.content, list):
        final_text = "".join(
            block.get("text", "")
            for block in last_message.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        final_text = last_message.content

    print("\n--- Agent Response ---")
    print(final_text)


if __name__ == "__main__":
    asyncio.run(main())