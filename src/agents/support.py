from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.rag.retriever import get_codebase_retriever_tool
from src.tools.mcp_loader import get_mcp_tools
from src.tools.custom_tools import (
    read_local_file,
    list_local_directory,
    system_health_check,
)

SUPPORT_SYSTEM_PROMPT = """You are the HabitatAI Support Agent.
Your role is local developer unblocking and repository diagnostics:
1. Inspect local configuration and source code using 'read_local_file' and 'list_local_directory'.
2. Check Git status/diffs using Git MCP tools.
3. Retrieve setup instructions and architectural rules via 'search_codebase_knowledge'.
"""

async def build_support_agent(model_name: str = "gemma-4-26b-a4b-it"):
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.0)
    
    git_tools = await get_mcp_tools(["git"])
    rag_tool = get_codebase_retriever_tool()

    tools = [
        *git_tools,
        read_local_file,
        list_local_directory,
        system_health_check,
        rag_tool,
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=SUPPORT_SYSTEM_PROMPT,
    )