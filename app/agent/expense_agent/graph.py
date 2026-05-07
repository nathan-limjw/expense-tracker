from langgraph.graph import END, START, StateGraph

from app.agent.expense_agent.nodes import (
    decision_node,
    extraction_node,
    validation_node,
)
from app.agent.expense_agent.schemas import ExpenseAgentState
from app.schemas.expense_schema import ExpenseCreate


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
            "input": ExpenseCreate(
                description="Spend $5 on lunch",
                user_id="c453f22b-f000-4102-a083-3be74a6ce959",
            ),
            "iterations": 0,
        }
    )
