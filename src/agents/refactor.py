from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.rag.retriever import get_codebase_retriever_tool
from src.tools.custom_tools import (
    read_local_file,
    write_local_file,
    list_local_directory,
    github_commit_file,
    github_create_pull_request,
)
from src.tools.mcp_loader import get_mcp_tools

REFACTOR_SYSTEM_PROMPT = """You are the HabitatAI Refactoring Agent.
Your role is continuous repository health and technical debt reduction:
1. Scan local files via 'read_local_file' and 'list_local_directory' for deprecated patterns, missing docstrings, and type hints.
2. Cross-reference repository standards using 'search_codebase_knowledge'.
3. Formulate minimal, non-breaking refactoring changes.
4. Stage refactor changes on clean feature branches using 'github_commit_file' and open pull requests via 'github_create_pull_request'.
"""


async def build_refactor_agent(model_name: str = "gemini-3.5-flash"):
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.0, max_retries = 2,  
        timeout=30.0)

    git_tools = await get_mcp_tools(["git"])
    rag_tool = get_codebase_retriever_tool()

    tools = [
        *git_tools,
        read_local_file,
        write_local_file,
        list_local_directory,
        github_commit_file,
        github_create_pull_request,
        rag_tool,
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=REFACTOR_SYSTEM_PROMPT,
    )
