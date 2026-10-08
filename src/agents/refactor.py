from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.rag.retriever import get_codebase_retriever_tool
from src.tools.mcp_loader import get_mcp_tools

REFACTOR_SYSTEM_PROMPT = """You are the HabitatAI Refactoring Agent.
Your role is continuous repository health and technical debt reduction:
1. Scan local files via filesystem tools for deprecated APIs and obsolete conventions.
2. Cross-reference repository standards using 'search_codebase_knowledge'.
3. Formulate minimal, non-breaking refactoring changes.
4. Coordinate with Git and GitHub MCP tools to create refactor branches and submit PRs.
"""


async def build_refactor_agent(model_name: str = "gemma-4-26b-a4b-it"):
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)

    mcp_tools = await get_mcp_tools(["filesystem", "git", "github"])
    rag_tool = get_codebase_retriever_tool()
    tools = [*mcp_tools, rag_tool]

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=REFACTOR_SYSTEM_PROMPT,
    )