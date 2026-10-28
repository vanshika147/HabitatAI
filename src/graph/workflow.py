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


async def create_sdlc_graph():
    dev_agent = await build_developer_agent()
    support_agent = await build_support_agent()
    refactor_agent = await build_refactor_agent()

    async def developer_node(state: AgentState):
        result = await dev_agent.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"], "next_agent": "developer"}

    async def support_node(state: AgentState):
        result = await support_agent.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"], "next_agent": "support"}

    async def refactor_node(state: AgentState):
        result = await refactor_agent.ainvoke({"messages": state["messages"]})
        return {"messages": result["messages"], "next_agent": "refactor"}

    builder = StateGraph(AgentState)
    builder.add_node("developer", developer_node)
    builder.add_node("support", support_node)
    builder.add_node("refactor", refactor_node)

    # Dynamic keyword router
    def route_task(state: AgentState) -> Literal["developer", "support", "refactor"]:
        last_msg_text = _get_text_content(state["messages"][-1]).lower()
        if any(keyword in last_msg_text for keyword in ["refactor", "clean", "type hint", "debt", "lint"]):
            return "refactor"
        if any(keyword in last_msg_text for keyword in ["status", "diff", "broken", "health", "why", "help"]):
            return "support"
        return "developer"

    builder.add_conditional_edges(START, route_task)
    builder.add_edge("developer", END)
    builder.add_edge("support", END)
    builder.add_edge("refactor", END)

    return builder.compile()