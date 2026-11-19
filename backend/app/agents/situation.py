"""
Situation Agent - RULE-BASED (deterministic on purpose).

Computes per-zone severity from a disaster event using explicit formulas,
not a model call. This step needs to be reliable and testable, so it stays
rule-based - see inference.py for the one place a real LLM call is used.
"""
import math
from ..models import ZoneStatus


def compute_flood_severity(zone, rainfall_mm):
    # 60mm/hr sustained is treated as saturating ("very heavy rain" by IMD categories)
    intensity = min(rainfall_mm / 60.0, 1.0)
    # elevation only partially offsets risk (0.4 weight) - even a moderately elevated
    # zone with poor drainage/high flood_risk_score can still flood badly
    return round(intensity * zone.flood_risk_score * (1 - 0.4 * zone.elevation_score), 4)


def compute_earthquake_severity(zone, epicenter_zone, magnitude):
    magnitude_factor = min(magnitude / 9.0, 1.0)
    distance = math.hypot(zone.x - epicenter_zone.x, zone.y - epicenter_zone.y)
    distance_decay = 1 / (1 + distance / 100.0)
    return round(magnitude_factor * zone.building_density_score * distance_decay, 4)


def label_from_score(score):
    if score < 0.30:
        return "LOW"
    if score < 0.55:
        return "MODERATE"
    if score < 0.80:
        return "HIGH"
    return "CRITICAL"


def run_situation_agent(db, event, zones):
    """Returns list of dicts and persists ZoneStatus rows."""
    results = []
    epicenter_zone = None
    if event.type == "earthquake":
        epicenter_id = event.params.get("epicenter_zone_id")
        epicenter_zone = next((z for z in zones if z.id == epicenter_id), zones[0])

    for zone in zones:
        if event.type == "flood":
            score = compute_flood_severity(zone, event.params.get("rainfall_mm", 0))
        elif event.type == "earthquake":
            score = compute_earthquake_severity(zone, epicenter_zone, event.params.get("magnitude", 5))
        else:
            score = 0.0

        label = label_from_score(score)
        affected = int(zone.population * min(score, 1.0))
        # More extreme scores get a higher confidence label in this simple model -
        # a real system would derive this from data completeness/sensor coverage.
        confidence = round(min(0.55 + 0.4 * score, 0.95), 2)

        status = ZoneStatus(
            zone_id=zone.id, event_id=event.id, severity_score=score,
            severity_label=label, affected_population_est=affected,
            confidence=confidence,
        )
        db.add(status)
        results.append({
            "zone_id": zone.id, "zone_name": zone.name, "severity_score": score,
            "severity_label": label, "affected_population_est": affected,
            "confidence": confidence,
        })

    db.commit()
    return results
