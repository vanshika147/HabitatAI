import truststore
truststore.inject_into_ssl()

import asyncio
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from src.graph.workflow import create_sdlc_graph, _get_text_content

load_dotenv()


async def main():
    print("=" * 60)
    print("  HabitatAI: Multi-Agent Autonomous SDLC Assistant")
    print("  (Stateless Mode | Fast-Fail Active)")
    print("  Type 'exit' or 'quit' to terminate")
    print("=" * 60)

    print("\nInitializing orchestrator graph and compiling agents...")
    graph = await create_sdlc_graph()
    print("All agents online and graph compiled. Ready.\n")

    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit", "q"]:
                print("Shutting down HabitatAI session. Goodbye!")
                break

            current_messages = [HumanMessage(content=user_input)]

            print("\n[Routing & Executing...]")
            active_node = "agent"
            result_messages = []

            async for chunk in graph.astream(
                {"messages": current_messages}, 
                stream_mode="updates"
            ):
                for node_name, state_update in chunk.items():
                    active_node = node_name
                    print(f"  ↳ Finished Node: [{node_name.upper()}]")
                    if "messages" in state_update:
                        result_messages = state_update["messages"]

            if result_messages:
                last_msg = result_messages[-1]
                content_str = _get_text_content(last_msg)

                print(f"\n[{active_node.upper()} AGENT RESPONSE]")
                print("-" * 60)
                print(content_str)
                print("-" * 60 + "\n")
            else:
                print("\n[Notice]: Task completed without returning response messages.\n")

        except KeyboardInterrupt:
            print("\nSession interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n[Execution Error]: {str(e)}\n")


if __name__ == "__main__":
    asyncio.run(main())