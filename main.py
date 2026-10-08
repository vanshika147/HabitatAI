import asyncio
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents import (
    build_developer_agent,
    build_refactor_agent,
    build_support_agent,
)

load_dotenv()

ROUTER_PROMPT = PromptTemplate.from_template(
    """Classify the following software engineering task into exactly one category:
- 'developer': Implementing new features, fixing tickets, opening PRs, GitHub issue workflows.
- 'support': Debugging local environments, dependency issues, build failures, runbook questions.
- 'refactor': Identifying technical debt, dead code cleanup, modernizing legacy packages.

Respond with ONLY the category name ('developer', 'support', or 'refactor').

Task: {task}
Category:"""
)


async def main():
    print("Initializing HabitatAI Gemini agents...")

    developer_executor = await build_developer_agent()
    support_executor = await build_support_agent()
    refactor_executor = await build_refactor_agent()

    router_chain = (
        ROUTER_PROMPT
        | ChatGoogleGenerativeAI(model="gemma-4-26b-a4b-it", temperature=0.0)
        | StrOutputParser()
    )

    agent_registry = {
        "developer": developer_executor,
        "support": support_executor,
        "refactor": refactor_executor,
    }

    print("✅ All agents online. Running diagnostic test query...\n")

    test_query = "My build fails with an import error when loading chroma_db. Check our codebase and help me resolve it."

    category = (await router_chain.ainvoke({"task": test_query})).strip().lower()
    selected_agent = agent_registry.get(category, support_executor)

    print(f"\n[Router] Task routed to: {category.upper()} AGENT")
    response = await selected_agent.ainvoke(
        {"messages": [("user", test_query)]}
    )

    last_message = response["messages"][-1]

    if isinstance(last_message.content, list):
        final_text = "".join(
            block.get("text", "")
            for block in last_message.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    else:
        final_text = last_message.content

    print("\n--- Response ---")
    print(final_text)


if __name__ == "__main__":
    asyncio.run(main())