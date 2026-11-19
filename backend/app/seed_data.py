"""
Seed data for SAATH Crisis Commander.
Zones are approximate real Nagpur localities, laid out on a simplified
800x600 simulated grid (not real lat/lng) so the frontend can render them
as a schematic SVG map rather than depending on a real map provider.
"""
from .models import Zone, Road, Resource
from datetime import datetime

ZONES = [
    dict(id=1, name="Zingabai Takli", population=6000, x=420, y=70,
         flood_risk_score=0.55, elevation_score=0.60, building_density_score=0.30,
         shelter_capacity=300, is_shelter_hub=False),
    dict(id=2, name="Jaripatka", population=9500, x=440, y=170,
         flood_risk_score=0.50, elevation_score=0.55, building_density_score=0.50,
         shelter_capacity=400, is_shelter_hub=False),
    dict(id=3, name="Wadi - Katol Road (RBU Campus Area)", population=12000, x=140, y=240,
         flood_risk_score=0.90, elevation_score=0.20, building_density_score=0.55,
         shelter_capacity=500, is_shelter_hub=False),
    dict(id=4, name="Nandanvan", population=15000, x=650, y=300,
         flood_risk_score=0.40, elevation_score=0.50, building_density_score=0.75,
         shelter_capacity=600, is_shelter_hub=False),
    dict(id=5, name="Sakkardara", population=8000, x=470, y=420,
         flood_risk_score=0.60, elevation_score=0.40, building_density_score=0.55,
         shelter_capacity=350, is_shelter_hub=False),
    dict(id=6, name="Dighori", population=7000, x=660, y=470,
         flood_risk_score=0.45, elevation_score=0.50, building_density_score=0.50,
         shelter_capacity=300, is_shelter_hub=False),
    dict(id=7, name="Pratap Nagar", population=13000, x=300, y=400,
         flood_risk_score=0.35, elevation_score=0.65, building_density_score=0.80,
         shelter_capacity=1000, is_shelter_hub=True),
    dict(id=8, name="Manewada", population=9000, x=410, y=560,
         flood_risk_score=0.50, elevation_score=0.45, building_density_score=0.60,
         shelter_capacity=350, is_shelter_hub=False),
]

# Pratap Nagar (id=7) is the designated relief/shelter hub and resource HQ
# for routing purposes - central, highest infrastructure density.
HQ_ZONE_ID = 7

ROADS = [
    dict(id=1, name="NH Link 1", zone_a_id=1, zone_b_id=2, status="open"),
    dict(id=2, name="Kamptee Road Link", zone_a_id=2, zone_b_id=4, status="open"),
    dict(id=3, name="Ring Road West", zone_a_id=2, zone_b_id=3, status="open"),
    dict(id=4, name="Katol Road", zone_a_id=3, zone_b_id=7, status="open"),
    dict(id=5, name="Central Avenue", zone_a_id=7, zone_b_id=5, status="open"),
    dict(id=6, name="Bridge-2", zone_a_id=5, zone_b_id=4, status="open"),
    dict(id=7, name="East Link", zone_a_id=5, zone_b_id=6, status="open"),
    dict(id=8, name="NH Link 2", zone_a_id=4, zone_b_id=6, status="open"),
    dict(id=9, name="South Link", zone_a_id=7, zone_b_id=8, status="open"),
    dict(id=10, name="Manewada Road", zone_a_id=5, zone_b_id=8, status="open"),
]

RESOURCE_COUNTS = {
    "ambulance": 6,
    "rescue_team": 4,
    "food_kit_batch": 5,
    "water_tanker": 3,
}


def seed_if_empty(db):
    if db.query(Zone).first() is not None:
        return  # already seeded

    for z in ZONES:
        db.add(Zone(**z))
    db.commit()

    for r in ROADS:
        db.add(Road(**r))
    db.commit()

    for rtype, count in RESOURCE_COUNTS.items():
        for _ in range(count):
            db.add(Resource(type=rtype, status="available",
                             home_zone_id=HQ_ZONE_ID, current_zone_id=HQ_ZONE_ID))
    db.commit()


def wipe_and_reseed(db):
    from .models import (ZoneStatus, Action, AgentDecision, Notification,
                          IncidentLog, FieldReport, DisasterEvent)
    db.query(ZoneStatus).delete()
    db.query(Action).delete()
    db.query(AgentDecision).delete()
    db.query(Notification).delete()
    db.query(IncidentLog).delete()
    db.query(FieldReport).delete()
    db.query(DisasterEvent).delete()
    db.commit()

    for z in db.query(Zone).all():
        z.field_network_down = False
    for r in db.query(Road).all():
        r.status = "open"
    for res in db.query(Resource).all():
        res.status = "available"
        res.current_zone_id = res.home_zone_id
        res.assigned_action_id = None
    db.commit()
