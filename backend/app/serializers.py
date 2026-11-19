from .models import Zone, ZoneStatus, Road, Resource, Action, AgentDecision, Notification, IncidentLog


def zone_dict(zone, latest_status=None):
    d = {
        "id": zone.id, "name": zone.name, "population": zone.population,
        "x": zone.x, "y": zone.y, "shelter_capacity": zone.shelter_capacity,
        "is_shelter_hub": zone.is_shelter_hub, "field_network_down": zone.field_network_down,
        "severity_label": "LOW", "severity_score": 0.0,
        "affected_population_est": 0, "confidence": 0.0,
    }
    if latest_status:
        d.update({
            "severity_label": latest_status.severity_label,
            "severity_score": latest_status.severity_score,
            "affected_population_est": latest_status.affected_population_est,
            "confidence": latest_status.confidence,
        })
    return d


def road_dict(road):
    return {"id": road.id, "name": road.name, "zone_a_id": road.zone_a_id,
            "zone_b_id": road.zone_b_id, "status": road.status}


def action_dict(action, zone_name=None):
    return {
        "id": action.id, "type": action.type, "resource_type": action.resource_type,
        "quantity": action.quantity, "target_zone_id": action.target_zone_id,
        "target_zone_name": zone_name, "priority": action.priority, "status": action.status,
        "route_valid": action.route_valid, "eta_minutes": action.eta_minutes,
        "is_evacuation": action.is_evacuation, "initiated_by_role": action.initiated_by_role,
        "approved_by_role": action.approved_by_role,
        "created_at": action.created_at.isoformat() if action.created_at else None,
    }


def decision_dict(d):
    return {
        "id": d.id, "agent_name": d.agent_name, "input_signals": d.input_signals,
        "reasoning_summary": d.reasoning_summary, "output": d.output,
        "confidence": d.confidence, "linked_action_id": d.linked_action_id,
        "timestamp": d.timestamp.isoformat() if d.timestamp else None,
    }


def notification_dict(n, zone_name=None):
    return {
        "id": n.id, "recipient_role": n.recipient_role, "need_type": n.need_type,
        "message": n.message, "reasoning": n.reasoning, "confidence": n.confidence,
        "estimated_quantity": n.estimated_quantity, "zone_id": n.zone_id,
        "zone_name": zone_name, "status": n.status,
        "timestamp": n.timestamp.isoformat() if n.timestamp else None,
    }


def incident_dict(i):
    return {"id": i.id, "message": i.message, "icon": i.icon,
            "timestamp": i.timestamp.isoformat() if i.timestamp else None}


def resource_summary(db):
    types = ["ambulance", "rescue_team", "food_kit_batch", "water_tanker"]
    summary = {}
    for t in types:
        total = db.query(Resource).filter(Resource.type == t).count()
        deployed = db.query(Resource).filter(Resource.type == t, Resource.status == "deployed").count()
        available = db.query(Resource).filter(Resource.type == t, Resource.status == "available").count()
        unavailable = db.query(Resource).filter(Resource.type == t, Resource.status == "unavailable").count()
        summary[t] = {"total": total, "deployed": deployed, "available": available, "unavailable": unavailable}
    return summary
