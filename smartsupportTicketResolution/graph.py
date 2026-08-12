from typing import TypedDict

from langgraph.graph import StateGraph, END

from ai_agent import ai_analysis


class TicketState(TypedDict, total=False):
    subject: str
    description: str
    category: str
    priority: str
    sentiment: str
    team: str
    suggested_resolution: str


def analyze_ticket(state: TicketState):
    result = ai_analysis(
        state["subject"],
        state["description"]
    )
    return result


def build_graph():
    workflow = StateGraph(TicketState)

    workflow.add_node("analyze_ticket", analyze_ticket)

    workflow.set_entry_point("analyze_ticket")
    workflow.add_edge("analyze_ticket", END)

    return workflow.compile()
