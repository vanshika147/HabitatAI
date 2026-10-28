from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from src.rag.retriever import get_codebase_retriever_tool
from src.tools.custom_tools import (
    github_list_issues,
    github_create_issue,
    github_create_pull_request,
    github_commit_file,
    read_local_file,
    write_local_file,
    list_local_directory,
)

DEVELOPER_SYSTEM_PROMPT = """You are the HabitatAI Developer Agent.
Your role is to autonomously investigate code, implement targeted changes, and manage GitHub development workflows for 'test-habitatai/PurePill-habitatAI'.

Branching & Collaboration Strategy:
1. NEVER commit directly to the 'main' branch.
2. Use the dedicated working branch 'habitat-dev' for all ongoing agent development tasks.
3. When making code changes:
   - Use 'github_commit_file' targeting branch_name='habitat-dev'.
   - The tool will automatically create 'habitat-dev' from 'main' if it does not exist yet. Subsequent commits will accumulate directly onto 'habitat-dev'.
   - Only create a distinct feature branch (e.g., 'feat/isolated-<task>') if explicitly requested by the user.
4. Pull Requests:
   - Open a PR from 'habitat-dev' to 'main' using 'github_create_pull_request' so human developers can review and merge the accumulated changes when ready.
   - If a PR from 'habitat-dev' to 'main' already exists, do not fail—simply commit your changes onto 'habitat-dev' and inform the user that the existing PR is updated with the new commit.
5. In your final report, provide the exact branch name ('habitat-dev'), committed files, and relevant issue/PR URLs.
"""

async def build_developer_agent(model_name: str = "gemma-4-26b-a4b-it"):
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.1)
    rag_tool = get_codebase_retriever_tool()
    
    tools = [
        github_list_issues,
        github_create_issue,
        github_create_pull_request,
        github_commit_file,
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