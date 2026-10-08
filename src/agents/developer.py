from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.rag.retriever import get_codebase_retriever_tool
from src.tools.custom_tools import (
    github_list_issues,
    github_create_issue,
    github_create_pull_request,
    read_local_file,
    write_local_file,
    list_local_directory,
)

DEVELOPER_SYSTEM_PROMPT = """You are the HabitatAI Developer Agent.
Your responsibility is autonomous Ticket-to-PR development on 'test-habitatai/PurePill-habitatAI'.

Available Capabilities:
1. Query indexed codebase patterns with 'search_codebase_knowledge'.
2. Read, list, and write local files via 'read_local_file', 'list_local_directory', 'write_local_file'.
3. Inspect and manage issues/PRs using 'github_list_issues', 'github_create_issue', 'github_create_pull_request'.
"""

async def build_developer_agent(model_name: str = "gemma-4-26b-a4b-it"):
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
    rag_tool = get_codebase_retriever_tool()
    
    tools = [
        github_list_issues,
        github_create_issue,
        github_create_pull_request,
        read_local_file,
        write_local_file,
        list_local_directory,
        rag_tool,
    ]

    return create_react_agent(
        model=llm,
        tools=tools,
        prompt=DEVELOPER_SYSTEM_PROMPT,
    )