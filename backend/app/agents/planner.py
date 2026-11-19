"""
Response Planner - RULE-BASED aggregation step.

Doesn't decide anything new - it just summarizes what Resource + Routing
agents produced into a final ranked plan, and writes the AgentDecision
log entries that make the whole pipeline auditable.
"""
from ..models import AgentDecision


def log_decision(db, agent_name, input_signals, reasoning_summary, output, confidence=None, linked_action_id=None):
    decision = AgentDecision(
        agent_name=agent_name, input_signals=input_signals,
        reasoning_summary=reasoning_summary, output=output,
        confidence=confidence, linked_action_id=linked_action_id,
    )
    db.add(decision)
    db.commit()
    return decision


def run_response_planner(db, event, zone_statuses, routed_proposals):
    critical = [z for z in zone_statuses if z["severity_label"] == "CRITICAL"]
    high = [z for z in zone_statuses if z["severity_label"] == "HIGH"]

    summary = (f"{len(critical)} critical zone(s), {len(high)} high-risk zone(s) identified. "
               f"{len(routed_proposals)} dispatch action(s) proposed, "
               f"{sum(1 for p in routed_proposals if not p['route_valid'])} blocked by road status.")

    log_decision(
        db, agent_name="response_planner",
        input_signals={"event_type": event.type, "zone_count": len(zone_statuses)},
        reasoning_summary=summary,
        output={"proposals": routed_proposals},
    )
    return summary
