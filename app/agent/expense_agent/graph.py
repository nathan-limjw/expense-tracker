from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

from app.agent.expense_agent.nodes import (
    decision_node,
    extraction_node,
    validation_node,
)
from app.agent.expense_agent.schemas import ExpenseAgentState


def create_extraction_agent_graph():
    builder = StateGraph(ExpenseAgentState)

    builder.add_node("extraction", extraction_node)
    builder.add_node("validation", validation_node)

    builder.add_edge(START, "extraction")
    builder.add_edge("extraction", "validation")
    builder.add_conditional_edges(
        "validation", decision_node, {"END": END, "extraction": "extraction"}
    )

    graph = builder.compile()

    return graph


if __name__ == "__main__":
    graph = create_extraction_agent_graph()
    response = graph.invoke(
        {
            "user_id": "kim",
            "messages": [HumanMessage("Spent -20 on koufu lunch 3 days ago")],
            "iterations": 0,
        }
    )
