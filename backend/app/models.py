from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, JSON
from datetime import datetime
from .database import Base


class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    population = Column(Integer, nullable=False)
    x = Column(Float, nullable=False)
    y = Column(Float, nullable=False)
    flood_risk_score = Column(Float, default=0.0)
    elevation_score = Column(Float, default=0.0)
    building_density_score = Column(Float, default=0.0)
    shelter_capacity = Column(Integer, default=0)
    is_shelter_hub = Column(Boolean, default=False)
    field_network_down = Column(Boolean, default=False)


class Road(Base):
    __tablename__ = "roads"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    zone_a_id = Column(Integer, ForeignKey("zones.id"))
    zone_b_id = Column(Integer, ForeignKey("zones.id"))
    status = Column(String, default="open")  # open / blocked


class Resource(Base):
    __tablename__ = "resources"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # ambulance, rescue_team, food_kit_batch, water_tanker
    status = Column(String, default="available")  # available, deployed, unavailable
    home_zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    current_zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    assigned_action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)


class DisasterEvent(Base):
    __tablename__ = "disaster_events"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # flood, earthquake
    params = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")


class ZoneStatus(Base):
    __tablename__ = "zone_statuses"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    event_id = Column(Integer, ForeignKey("disaster_events.id"), nullable=True)
    severity_score = Column(Float, default=0.0)
    severity_label = Column(String, default="LOW")
    affected_population_est = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow)


class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # dispatch, relief_dispatch
    resource_type = Column(String, nullable=True)
    quantity = Column(Integer, default=1)
    target_zone_id = Column(Integer, ForeignKey("zones.id"))
    priority = Column(String, default="MEDIUM")
    status = Column(String, default="pending")  # pending, approved, rejected
    route_valid = Column(Boolean, default=True)
    eta_minutes = Column(Integer, nullable=True)
    initiated_by_role = Column(String, default="system")
    approved_by_role = Column(String, nullable=True)
    is_evacuation = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentDecision(Base):
    __tablename__ = "agent_decisions"
    id = Column(Integer, primary_key=True, index=True)
    agent_name = Column(String, nullable=False)
    input_signals = Column(JSON, default=dict)
    reasoning_summary = Column(Text, default="")
    output = Column(JSON, default=dict)
    confidence = Column(Float, nullable=True)
    linked_action_id = Column(Integer, ForeignKey("actions.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    recipient_role = Column(String, nullable=False)
    need_type = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    reasoning = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    estimated_quantity = Column(Integer, nullable=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=True)
    status = Column(String, default="pending")  # pending, actioned, rejected
    source_decision_id = Column(Integer, ForeignKey("agent_decisions.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


class IncidentLog(Base):
    __tablename__ = "incident_log"
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    icon = Column(String, default="info")
    timestamp = Column(DateTime, default=datetime.utcnow)


class FieldReport(Base):
    __tablename__ = "field_reports"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id"))
    message = Column(String, nullable=False)
    client_timestamp = Column(DateTime, nullable=True)
    server_synced_at = Column(DateTime, default=datetime.utcnow)
    was_queued = Column(Boolean, default=False)
