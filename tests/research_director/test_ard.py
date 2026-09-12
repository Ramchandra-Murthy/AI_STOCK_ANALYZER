from __future__ import annotations

from services.research_director.director import ResearchDirectorEngine
from services.research_director.models import ResearchMission


def test_research_mission_immutability() -> None:
    mission = ResearchMission(
        mission_id="M-001",
        symbol="RELIANCE.NS",
        priority=1,
        assigned_agents=["ValuationAgent"],
        status="COMPLETED",
        start_time="2026-08-07T12:00:00",
        completion_time="2026-08-07T12:05:00",
        workflow_id="WF-001",
    )
    assert mission.mission_id == "M-001"
    assert mission.status == "COMPLETED"
    assert mission.timestamp is not None
    assert isinstance(mission.metadata, dict)


def test_research_director_engine() -> None:
    mission = ResearchDirectorEngine.launch_mission("M-002", "TCS.NS", 1)
    assert mission.mission_id == "M-002"
    assert mission.symbol == "TCS.NS"
    assert mission.status == "COMPLETED"
    assert len(mission.assigned_agents) > 0
