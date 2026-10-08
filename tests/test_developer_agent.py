import asyncio
from dotenv import load_dotenv
from src.agents.developer import build_developer_agent

load_dotenv()

async def main():
    print("Testing 100% Python-Native Developer Agent...")
    developer_agent = await build_developer_agent()
    
    test_prompt = ("Create a new issue in our repository titled 'Test Ticket from HabitatAI' "
    "with the body 'HabitatAI Developer Agent integration and tool calling verified successfully.'")
    
    response = await developer_agent.ainvoke({
        "messages": [("user", test_prompt)]
    })
    
    print("\n--- Agent Response ---")
    print(response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())