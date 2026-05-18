from langgraph.graph import END, START, StateGraph

from app.agent.report_agent.nodes.accountant_node import accountant_node
from app.agent.report_agent.nodes.analyst_node import analyst_node
from app.agent.report_agent.nodes.presenter_node import presenter_node
from app.agent.report_agent.nodes.visualiser_node import visualiser_node
from app.agent.report_agent.schemas import ReportAgentState


def create_report_agent_graph():
    builder = StateGraph(ReportAgentState)

    builder.add_node("accountant", accountant_node)
    builder.add_node("analyst", analyst_node)
    builder.add_node("visualiser", visualiser_node)
    builder.add_node("presenter", presenter_node)

    builder.add_edge(START, "accountant")
    builder.add_edge("accountant", "analyst")
    builder.add_edge("accountant", "visualiser")
    builder.add_edge("analyst", "presenter")
    builder.add_edge("visualiser", "presenter")
    builder.add_edge("presenter", END)

    graph = builder.compile()

    return graph
