from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents import (
    profile_agent,
    job_matching_agent,
    skill_gap_agent,
    roadmap_agent,
    interview_agent,
    final_career_agent,
)


class CareerState(TypedDict):
    profile: dict
    jobs_text: str
    profile_analysis: str
    job_matching: str
    skill_gap: str
    roadmap: str
    interview: str
    final_report: str


def profile_node(state):
    return {"profile_analysis": profile_agent(state["profile"])}


def matching_node(state):
    return {
        "job_matching": job_matching_agent(
            state["profile"], state["jobs_text"]
        )
    }


def gap_node(state):
    return {
        "skill_gap": skill_gap_agent(
            state["profile"], state["job_matching"]
        )
    }


def roadmap_node(state):
    return {
        "roadmap": roadmap_agent(
            state["profile"], state["skill_gap"]
        )
    }


def interview_node(state):
    return {
        "interview": interview_agent(
            state["profile"], state["job_matching"]
        )
    }


def final_node(state):
    return {
        "final_report": final_career_agent(
            state["profile"],
            state["job_matching"],
            state["skill_gap"],
            state["roadmap"],
            state["interview"],
        )
    }


def build_graph():
    workflow = StateGraph(CareerState)

    workflow.add_node("profile_agent", profile_node)
    workflow.add_node("job_matching_agent", matching_node)
    workflow.add_node("skill_gap_agent", gap_node)
    workflow.add_node("roadmap_agent", roadmap_node)
    workflow.add_node("interview_agent", interview_node)
    workflow.add_node("final_agent", final_node)

    workflow.set_entry_point("profile_agent")

    workflow.add_edge("profile_agent", "job_matching_agent")
    workflow.add_edge("job_matching_agent", "skill_gap_agent")
    workflow.add_edge("skill_gap_agent", "roadmap_agent")
    workflow.add_edge("roadmap_agent", "interview_agent")
    workflow.add_edge("interview_agent", "final_agent")
    workflow.add_edge("final_agent", END)

    return workflow.compile()
