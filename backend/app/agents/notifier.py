"""
Notifier / Coordinator Agent - RULE-BASED routing table.

Maps an inferred need_type to the stakeholder role that owns that
resource domain. Deliberately a flat hardcoded dict for v1 - adding a
role/need mapping later is a one-line change, not a redesign.
"""
from ..models import Notification

NEED_TO_ROLE = {
    "food_kits": "food_officer",
    "water": "food_officer",
    "medical_supplies": "food_officer",  # would route to a Hospital role in a future version
}


def run_notifier_agent(db, zone, need_type, estimated_quantity, time_horizon_hours,
                        confidence, reasoning, source_decision_id):
    role = NEED_TO_ROLE.get(need_type, "food_officer")
    message = (f"Predicted {need_type.replace('_', ' ')} shortage in {zone.name} "
               f"within ~{time_horizon_hours}h (est. {estimated_quantity} units needed).")

    notification = Notification(
        recipient_role=role, need_type=need_type, message=message,
        reasoning=reasoning, confidence=confidence, estimated_quantity=estimated_quantity,
        zone_id=zone.id, status="pending", source_decision_id=source_decision_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
