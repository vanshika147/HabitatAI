from typing import Annotated, Literal
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.agents.developer import build_developer_agent
from src.agents.support import build_support_agent
from src.agents.refactor import build_refactor_agent


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    next_agent: str


def _get_text_content(msg: BaseMessage) -> str:
    """Safely extracts raw text from string or structured block lists."""
    if isinstance(msg.content, list):
        return "".join(
            block.get("text", "")
            for block in msg.content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(msg.content)


async def create_sdlc_graph(model_name: str = "gemini-3.5-flash"):
    print("  [Graph Build] Instantiating developer agent...")
    dev_agent = await build_developer_agent(model_name = model_name)
    print("  [Graph Build] Instantiating support agent...")
    support_agent = await build_support_agent(model_name= model_name)
    print("  [Graph Build] Instantiating refactor agent...")
    refactor_agent = await build_refactor_agent(model_name = model_name)

    async def developer_node(state: AgentState):
        print("\n  >>> [NODE: DEVELOPER] Starting execution with developer agent...")
        result = await dev_agent.ainvoke({"messages": state["messages"]})
        print("  >>> [NODE: DEVELOPER] Finished execution.")
        return {"messages": result["messages"], "next_agent": "developer"}

    async def support_node(state: AgentState):
        print("\n  >>> [NODE: SUPPORT] Starting execution with support agent...")
        result = await support_agent.ainvoke({"messages": state["messages"]})
        print("  >>> [NODE: SUPPORT] Finished execution.")
        return {"messages": result["messages"], "next_agent": "support"}

    async def refactor_node(state: AgentState):
        print("\n  >>> [NODE: REFACTOR] Starting execution with refactor agent...")
        result = await refactor_agent.ainvoke({"messages": state["messages"]})
        print("  >>> [NODE: REFACTOR] Finished execution.")
        return {"messages": result["messages"], "next_agent": "refactor"}

    builder = StateGraph(AgentState)
    builder.add_node("developer", developer_node)
    builder.add_node("support", support_node)
    builder.add_node("refactor", refactor_node)

    def route_task(state: AgentState) -> Literal["developer", "support", "refactor"]:
        last_msg_text = _get_text_content(state["messages"][-1]).lower()
        print(f"  [ROUTER] Evaluating last query: '{last_msg_text[:60]}...'")

        dev_action_keywords = ["pr", "pull request", "commit", "branch", "issue", "ticket", "habitat-dev"]
        if any(keyword in last_msg_text for keyword in dev_action_keywords):
            choice = "developer"

        elif any(keyword in last_msg_text for keyword in ["status", "diff", "broken", "health", "why", "help", "diagnos"]):
            choice = "support"

        elif any(keyword in last_msg_text for keyword in ["refactor", "clean", "type hint", "debt", "lint"]):
            choice = "refactor"
        else:
            choice = "developer"

        print(f"  [ROUTER] Decision -> Routing to: '{choice}'")
        return choice

    builder.add_conditional_edges(START, route_task)
    builder.add_edge("developer", END)
    builder.add_edge("support", END)
    builder.add_edge("refactor", END)

    return builder.compile()