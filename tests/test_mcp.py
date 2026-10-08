import asyncio
from dotenv import load_dotenv
from src.tools.mcp_loader import get_mcp_tools

load_dotenv()


async def main():
    print("Testing MCP Tool Loader...")
    print("\n1. Connecting to 'filesystem' MCP server...")
    try:
        fs_tools = await get_mcp_tools(["filesystem"])
        print(f"Loaded {len(fs_tools)} filesystem tools:")
        for tool in fs_tools:
            print(f"  - {tool.name}")
    except Exception as e:
        print(f"Failed to load filesystem tools: {e}")

    print("\n2. Connecting to 'git' MCP server...")
    try:
        git_tools = await get_mcp_tools(["git"])
        print(f"Loaded {len(git_tools)} git tools:")
        for tool in git_tools:
            print(f"  - {tool.name}")
    except Exception as e:
        print(f"Failed to load git tools: {e}")

    print("\n3. Connecting to 'github' MCP server...")
    try:
        gh_tools = await get_mcp_tools(["github"])
        print(f"Loaded {len(gh_tools)} github tools:")
        for tool in gh_tools:
            print(f"  - {tool.name}")
    except Exception as e:
        print(f"Failed to load github tools: {e}")


if __name__ == "__main__":
    asyncio.run(main())