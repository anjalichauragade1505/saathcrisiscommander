"""
Resource Agent - RULE-BASED.

Ranks zones by (severity * population) and proposes dispatch actions
against currently available resources. Creates pending Action rows -
nothing is committed until a human (Commander) approves it.
"""
from ..models import Resource, Action

EVACUATION_POP_THRESHOLD = 5000  # zones above this + CRITICAL are flagged as evacuation-scale


def run_resource_agent(db, zone_statuses, zones_by_id):
    proposals = []
    ranked = sorted(zone_statuses, key=lambda s: s["severity_score"] * s["affected_population_est"], reverse=True)

    for status in ranked:
        label = status["severity_label"]
        if label == "LOW":
            continue

        zone = zones_by_id[status["zone_id"]]
        is_evacuation = label == "CRITICAL" and zone.population >= EVACUATION_POP_THRESHOLD

        if label == "CRITICAL":
            wants = [("rescue_team", 2), ("ambulance", 2)]
            priority = "HIGH"
        elif label == "HIGH":
            wants = [("rescue_team", 1), ("ambulance", 1)]
            priority = "HIGH"
        else:  # MODERATE
            wants = [("ambulance", 1)]
            priority = "MEDIUM"

        for rtype, qty in wants:
            available = db.query(Resource).filter(
                Resource.type == rtype, Resource.status == "available"
            ).count()
            if available <= 0:
                continue
            actual_qty = min(qty, available)

            action = Action(
                type="dispatch", resource_type=rtype, quantity=actual_qty,
                target_zone_id=zone.id, priority=priority, status="pending",
                initiated_by_role="system", is_evacuation=is_evacuation,
            )
            db.add(action)
            db.flush()
            proposals.append({
                "action_id": action.id, "zone_id": zone.id, "zone_name": zone.name,
                "resource_type": rtype, "quantity": actual_qty, "priority": priority,
                "is_evacuation": is_evacuation,
            })

    db.commit()
    return proposals
