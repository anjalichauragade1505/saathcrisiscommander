"""
Orchestrator - runs the agent pipeline in sequence and writes the
incident log entries that power the Live Incident Feed panel.

Pipeline: Situation -> Resource -> Routing -> Response Planner
(Inference Agent runs separately, triggered by action approval - see
routes.py - because it only fires once a human approves an evacuation.)
"""
from ..models import Zone, IncidentLog
from .situation import run_situation_agent
from .resource import run_resource_agent
from .routing import run_routing_agent
from .planner import run_response_planner, log_decision


def log_incident(db, message, icon="info"):
    db.add(IncidentLog(message=message, icon=icon))
    db.commit()


def run_disaster_pipeline(db, event):
    zones = db.query(Zone).all()
    zones_by_id = {z.id: z for z in zones}

    zone_statuses = run_situation_agent(db, event, zones)
    log_decision(
        db, agent_name="situation_agent",
        input_signals={"event_type": event.type, "params": event.params},
        reasoning_summary=f"Computed severity for {len(zone_statuses)} zones using "
                           f"{'flood rainfall/drainage' if event.type == 'flood' else 'earthquake magnitude/distance/density'} formula.",
        output={"statuses": zone_statuses},
    )
    for zs in zone_statuses:
        if zs["severity_label"] in ("CRITICAL", "HIGH"):
            log_incident(db, f"{zs['zone_name']} flagged {zs['severity_label']} "
                              f"(~{zs['affected_population_est']} affected)", icon="alert")

    proposals = run_resource_agent(db, zone_statuses, zones_by_id)
    log_decision(
        db, agent_name="resource_agent",
        input_signals={"zones_considered": len(zone_statuses)},
        reasoning_summary=f"Proposed {len(proposals)} dispatch action(s) ranked by severity x population.",
        output={"proposals": proposals},
    )

    routed = run_routing_agent(db, proposals)
    log_decision(
        db, agent_name="routing_agent",
        input_signals={"proposals_checked": len(proposals)},
        reasoning_summary=f"Validated routes for {len(routed)} proposal(s) via BFS over road graph; "
                           f"{sum(1 for r in routed if not r['route_valid'])} unreachable.",
        output={"routed": routed},
    )
    for r in routed:
        if not r["route_valid"]:
            log_incident(db, f"No valid route to {r['zone_name']} - road network blocked", icon="alert")

    summary = run_response_planner(db, event, zone_statuses, routed)
    log_incident(db, f"Response plan updated: {summary}", icon="plan")

    return {"zone_statuses": zone_statuses, "proposals": routed, "summary": summary}
