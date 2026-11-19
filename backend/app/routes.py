
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .models import (
    Zone, ZoneStatus, Road, Resource, Action, AgentDecision,
    Notification, IncidentLog, DisasterEvent, FieldReport
)
from .schemas import (
    InjectEventRequest, NotificationRespondRequest,
    FieldReportRequest, FieldSyncRequest
)
from .seed_data import wipe_and_reseed, HQ_ZONE_ID
from .serializers import (
    zone_dict, road_dict, action_dict, decision_dict,
    notification_dict, incident_dict, resource_summary
)
from .agents.orchestrator import run_disaster_pipeline, log_incident
from .agents.routing import recheck_all_pending_routes
from .agents.inference import run_inference_agent
from .agents.notifier import run_notifier_agent
from .agents.planner import log_decision

router = APIRouter(prefix="/api")


def _latest_status_by_zone(db):
    statuses = db.query(ZoneStatus).order_by(
        ZoneStatus.updated_at.desc()
    ).all()

    latest = {}

    for s in statuses:
        if s.zone_id not in latest:
            latest[s.zone_id] = s

    return latest


def _compute_stats(db, zones, latest_status):

    critical_zones = sum(
        1 for z in zones
        if latest_status.get(z.id)
        and latest_status[z.id].severity_label == "CRITICAL"
    )

    affected = sum(
        s.affected_population_est
        for s in latest_status.values()
    )

    deployed = db.query(Resource).filter(
        Resource.status == "deployed"
    ).count()

    ongoing_ops = db.query(Action).filter(
        Action.status == "approved"
    ).count()

    avg_severity = (
        sum(s.severity_score for s in latest_status.values())
        / len(latest_status)
    ) if latest_status else 0

    response_score = max(
        0,
        min(100, int(100 - critical_zones * 12 - avg_severity * 25))
    )

    return {
        "critical_zones": critical_zones,
        "people_affected": affected,
        "resources_deployed": deployed,
        "ongoing_operations": ongoing_ops,
        "response_score": response_score,
    }


# =====================================================
# SIMULATION CONTROL
# =====================================================

@router.post("/simulation/reset")
def reset_simulation(db: Session = Depends(get_db)):

    wipe_and_reseed(db)

    log_incident(
        db,
        "Simulation reset.",
        icon="info"
    )

    return {"status": "reset"}


@router.post("/simulation/inject-event")
def inject_event(payload: InjectEventRequest, db: Session = Depends(get_db)):

    if payload.type == "flood":

        event = DisasterEvent(
            type="flood",
            params={"rainfall_mm": payload.rainfall_mm or 0}
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        log_incident(
            db,
            f"New flood event injected: {payload.rainfall_mm}mm/hr rainfall.",
            icon="flood"
        )

        result = run_disaster_pipeline(db, event)

        return {
            "status": "ok",
            "event_id": event.id,
            "result": result
        }

    if payload.type == "earthquake":

        if not payload.epicenter_zone_id:
            raise HTTPException(
                400,
                "epicenter_zone_id required for earthquake"
            )

        event = DisasterEvent(
            type="earthquake",
            params={
                "epicenter_zone_id": payload.epicenter_zone_id,
                "magnitude": payload.magnitude or 5.0
            }
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        epicenter = db.get(Zone, payload.epicenter_zone_id)

        log_incident(
            db,
            f"Earthquake event injected: magnitude {payload.magnitude} near {epicenter.name}.",
            icon="quake"
        )

        result = run_disaster_pipeline(db, event)

        return {
            "status": "ok",
            "event_id": event.id,
            "result": result
        }

    if payload.type == "road_block":

        road = db.get(Road, payload.road_id)

        if not road:
            raise HTTPException(404, "road not found")

        road.status = "blocked"
        db.commit()

        log_incident(
            db,
            f"Road '{road.name}' is now blocked.",
            icon="alert"
        )

        changed = recheck_all_pending_routes(db)

        if changed:
            log_incident(
                db,
                f"Routing Agent recalculated {len(changed)} affected plan(s).",
                icon="plan"
            )

        return {
            "status": "ok",
            "road_id": road.id,
            "affected_actions": changed
        }

    if payload.type == "road_clear":

        road = db.get(Road, payload.road_id)

        if not road:
            raise HTTPException(404, "road not found")

        road.status = "open"
        db.commit()

        log_incident(
            db,
            f"Road '{road.name}' has been cleared.",
            icon="info"
        )

        changed = recheck_all_pending_routes(db)

        return {
            "status": "ok",
            "road_id": road.id,
            "affected_actions": changed
        }

    if payload.type == "communication_failure":

        zone = db.get(Zone, payload.zone_id)

        if not zone:
            raise HTTPException(404, "zone not found")

        zone.field_network_down = True
        db.commit()

        log_incident(
            db,
            f"Communication failure in {zone.name} - field reports will queue locally.",
            icon="alert"
        )

        return {"status": "ok", "zone_id": zone.id}

    if payload.type == "connectivity_restored":

        zone = db.get(Zone, payload.zone_id)

        if not zone:
            raise HTTPException(404, "zone not found")

        zone.field_network_down = False
        db.commit()

        log_incident(
            db,
            f"Connectivity restored in {zone.name}.",
            icon="info"
        )

        return {"status": "ok", "zone_id": zone.id}

    raise HTTPException(
        400,
        f"unknown event type: {payload.type}"
    )


# =====================================================
# SIMULATION STATE
# =====================================================

@router.get("/simulation/state")
def get_state(db: Session = Depends(get_db)):

    zones = db.query(Zone).all()

    latest_status = _latest_status_by_zone(db)

    zones_out = [
        zone_dict(z, latest_status.get(z.id))
        for z in zones
    ]

    roads = [
        road_dict(r)
        for r in db.query(Road).all()
    ]

    pending_actions = db.query(Action).filter(
        Action.status == "pending"
    ).order_by(Action.created_at.desc()).all()

    zones_by_id = {z.id: z for z in zones}

    pending_out = [
        action_dict(a, zones_by_id[a.target_zone_id].name)
        for a in pending_actions
    ]

    incidents = db.query(IncidentLog).order_by(
        IncidentLog.timestamp.desc()
    ).limit(20).all()

    incidents_out = [
        incident_dict(i)
        for i in incidents
    ]

    agent_names = [
        "situation_agent",
        "resource_agent",
        "routing_agent",
        "response_planner",
        "inference_agent"
    ]

    activity = []

    for name in agent_names:

        latest = db.query(AgentDecision).filter(
            AgentDecision.agent_name == name
        ).order_by(
            AgentDecision.timestamp.desc()
        ).first()

        activity.append({
            "agent_name": name,
            "has_run": latest is not None,
            "reasoning_summary": latest.reasoning_summary if latest else None,
            "timestamp": latest.timestamp.isoformat() if latest else None,
        })

    stats = _compute_stats(db, zones, latest_status)

    resources = resource_summary(db)

    return {
        "zones": zones_out,
        "roads": roads,
        "pending_actions": pending_out,
        "incidents": incidents_out,
        "agent_activity": activity,
        "stats": stats,
        "resources": resources,
    }


# =====================================================
# ACTION APPROVAL - CLAUDE INFERENCE DEBUGGING
# =====================================================

@router.post("/actions/{action_id}/approve")
def approve_action(action_id: int, db: Session = Depends(get_db)):

    action = db.get(Action, action_id)

    if not action:
        raise HTTPException(404, "action not found")

    if action.status != "pending":
        raise HTTPException(400, "action already resolved")

    resources = db.query(Resource).filter(
        Resource.type == action.resource_type,
        Resource.status == "available"
    ).limit(action.quantity).all()

    for r in resources:
        r.status = "deployed"
        r.current_zone_id = action.target_zone_id
        r.assigned_action_id = action.id

    action.status = "approved"
    action.approved_by_role = "commander"

    db.commit()

    zone = db.get(Zone, action.target_zone_id)

    log_incident(
        db,
        f"Approved: {action.quantity}x {action.resource_type} -> {zone.name}.",
        icon="approved"
    )

    inference_result = None

    # DEBUG INFORMATION
    print("\n========== APPROVAL DEBUG ==========")
    print("Action ID:", action.id)
    print("Action type:", action.type)
    print("Resource type:", action.resource_type)
    print("Is evacuation:", action.is_evacuation)
    print("Target zone:", zone.name)
    print("====================================")

    if action.is_evacuation:

        print("EVACUATION DETECTED - CALLING INFERENCE AGENT")

        latest = db.query(ZoneStatus).filter(
            ZoneStatus.zone_id == zone.id
        ).order_by(
            ZoneStatus.updated_at.desc()
        ).first()

        severity_label = latest.severity_label if latest else "HIGH"

        disaster_type = "flood"

        latest_event = db.query(DisasterEvent).order_by(
            DisasterEvent.started_at.desc()
        ).first()

        if latest_event:
            disaster_type = latest_event.type

        try:

            result, inputs = run_inference_agent(
                zone,
                disaster_type,
                zone.population,
                severity_label
            )

            print("\n========== INFERENCE RESULT ==========")
            print("Result:", result)
            print("Fallback used:", result.get("was_fallback"))
            print("======================================\n")

            decision = log_decision(
                db,
                agent_name="inference_agent",
                input_signals=inputs,
                reasoning_summary=result["reasoning"],
                output=result,
                confidence=result.get("confidence"),
                linked_action_id=action.id,
            )

            notification = run_notifier_agent(
                db,
                zone,
                result["need_type"],
                result["estimated_quantity"],
                result["time_horizon_hours"],
                result["confidence"],
                result["reasoning"],
                decision.id,
            )

            fallback_note = (
                " (fallback estimate used)"
                if result.get("was_fallback")
                else ""
            )

            log_incident(
                db,
                f"Inference Agent predicted {result['need_type']} shortage in {zone.name}{fallback_note} - "
                f"{notification.recipient_role.replace('_', ' ')} notified.",
                icon="ai"
            )

            inference_result = {
                "decision": decision_dict(decision),
                "notification": notification_dict(notification, zone.name)
            }

        except Exception as e:

            print("\n========== INFERENCE ROUTE ERROR ==========")
            print("Error type:", type(e).__name__)
            print("Error details:", str(e))
            print("===========================================\n")

            raise

    else:

        print("NOT AN EVACUATION - INFERENCE AGENT NOT CALLED")

    return {
        "status": "approved",
        "action": action_dict(action, zone.name),
        "inference": inference_result
    }


# =====================================================
# ACTION REJECTION
# =====================================================

@router.post("/actions/{action_id}/reject")
def reject_action(action_id: int, db: Session = Depends(get_db)):

    action = db.get(Action, action_id)

    if not action:
        raise HTTPException(404, "action not found")

    if action.status != "pending":
        raise HTTPException(400, "action already resolved")

    action.status = "rejected"
    db.commit()

    zone = db.get(Zone, action.target_zone_id)

    log_incident(
        db,
        f"Rejected: {action.quantity}x {action.resource_type} -> {zone.name}.",
        icon="rejected"
    )

    return {
        "status": "rejected",
        "action": action_dict(action, zone.name)
    }


# =====================================================
# AGENT LOG / NOTIFICATIONS
# =====================================================

@router.get("/agent-log")
def get_agent_log(db: Session = Depends(get_db)):

    decisions = db.query(AgentDecision).order_by(
        AgentDecision.timestamp.desc()
    ).limit(100).all()

    return {
        "decisions": [
            decision_dict(d)
            for d in decisions
        ]
    }


@router.get("/notifications")
def get_notifications(role: str, db: Session = Depends(get_db)):

    notes = db.query(Notification).filter(
        Notification.recipient_role == role
    ).order_by(
        Notification.timestamp.desc()
    ).all()

    zones_by_id = {
        z.id: z.name
        for z in db.query(Zone).all()
    }

    return {
        "notifications": [
            notification_dict(n, zones_by_id.get(n.zone_id))
            for n in notes
        ]
    }


@router.post("/notifications/{notification_id}/respond")
def respond_notification(
    notification_id: int,
    payload: NotificationRespondRequest,
    db: Session = Depends(get_db)
):

    note = db.get(Notification, notification_id)

    if not note:
        raise HTTPException(404, "notification not found")

    if note.status != "pending":
        raise HTTPException(400, "notification already resolved")

    zone = db.get(Zone, note.zone_id)

    if not payload.approve:

        note.status = "rejected"
        db.commit()

        log_incident(
            db,
            f"Food Officer rejected relief dispatch to {zone.name}.",
            icon="rejected"
        )

        return {"status": "rejected"}

    resource_type = (
        "food_kit_batch"
        if note.need_type in ("food_kits",)
        else "water_tanker"
    )

    available = db.query(Resource).filter(
        Resource.type == resource_type,
        Resource.status == "available"
    ).all()

    qty = min(
        len(available),
        max(1, note.estimated_quantity // 500 if note.estimated_quantity else 1)
    )

    for r in available[:qty]:
        r.status = "deployed"
        r.current_zone_id = note.zone_id

    action = Action(
        type="relief_dispatch",
        resource_type=resource_type,
        quantity=qty,
        target_zone_id=note.zone_id,
        priority="MEDIUM",
        status="approved",
        initiated_by_role="food_officer",
        approved_by_role="food_officer",
    )

    db.add(action)

    note.status = "actioned"

    db.commit()

    log_incident(
        db,
        f"Food Officer approved relief dispatch: {qty}x {resource_type} -> {zone.name}.",
        icon="approved"
    )

    return {
        "status": "actioned",
        "action": action_dict(action, zone.name)
    }


# =====================================================
# RISK FORECAST
# =====================================================

@router.get("/risk-forecast")
def get_risk_forecast(db: Session = Depends(get_db)):

    latest_status = _latest_status_by_zone(db)

    if not latest_status:
        base = 0.1
    else:
        base = max(
            s.severity_score
            for s in latest_status.values()
        )

    # Synthetic forward curve, not a real weather forecast.
    points = []

    for hour in [0, 1, 2, 3, 4, 5, 6]:

        factor = (
            1 + 0.15 * hour
            if hour <= 3
            else 1.45 - 0.1 * (hour - 3)
        )

        risk = max(
            0,
            min(1, base * factor)
        )

        points.append({
            "hour": hour,
            "risk": round(risk, 3)
        })

    return {"forecast": points}


# =====================================================
# FIELD REPORTING
# =====================================================

@router.post("/field/report")
def field_report(payload: FieldReportRequest, db: Session = Depends(get_db)):

    zone = db.get(Zone, payload.zone_id)

    if not zone:
        raise HTTPException(404, "zone not found")

    if zone.field_network_down:
        raise HTTPException(503, "network_unavailable")

    fr = FieldReport(
        zone_id=zone.id,
        message=payload.message,
        client_timestamp=payload.client_timestamp or datetime.utcnow(),
        server_synced_at=datetime.utcnow(),
        was_queued=False,
    )

    db.add(fr)

    log_incident(
        db,
        f"Field report from {zone.name}: {payload.message}",
        icon="field"
    )

    db.commit()

    return {
        "status": "sent",
        "report_id": fr.id
    }


@router.post("/field/sync")
def field_sync(payload: FieldSyncRequest, db: Session = Depends(get_db)):

    zone = db.get(Zone, payload.zone_id)

    if not zone:
        raise HTTPException(404, "zone not found")

    synced = []

    for item in payload.reports:

        now = datetime.utcnow()

        fr = FieldReport(
            zone_id=zone.id,
            message=item.message,
            client_timestamp=item.client_timestamp,
            server_synced_at=now,
            was_queued=True,
        )

        db.add(fr)

        delay_seconds = (
            now - item.client_timestamp
        ).total_seconds()

        synced.append({
            "message": item.message,
            "delay_seconds": round(delay_seconds, 1)
        })

    if synced:

        avg_delay = sum(
            s["delay_seconds"]
            for s in synced
        ) / len(synced)

        log_incident(
            db,
            f"{len(synced)} queued field report(s) from {zone.name} synced "
            f"(avg delay {round(avg_delay, 1)}s).",
            icon="sync"
        )

    db.commit()

    return {
        "status": "synced",
        "synced": synced
    }


@router.get("/field/tasks")
def field_tasks(zone_id: int, db: Session = Depends(get_db)):

    actions = db.query(Action).filter(
        Action.target_zone_id == zone_id,
        Action.status == "approved"
    ).all()

    zone = db.get(Zone, zone_id)

    return {
        "tasks": [
            action_dict(a, zone.name if zone else None)
            for a in actions
        ]
    }


@router.get("/zones")
def list_zones(db: Session = Depends(get_db)):

    zones = db.query(Zone).all()

    latest_status = _latest_status_by_zone(db)

    return {
        "zones": [
            zone_dict(z, latest_status.get(z.id))
            for z in zones
        ]
    }


@router.get("/roads")
def list_roads(db: Session = Depends(get_db)):

    return {
        "roads": [
            road_dict(r)
            for r in db.query(Road).all()
        ]
    }
