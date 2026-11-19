"""
Inference Agent - THE ONE REAL LLM CALL IN THIS SYSTEM.

Everything else in this pipeline is deterministic rule-based logic, on
purpose - it needs to be reliable and explainable. This step is different:
given an approved evacuation/dispatch action, it has to infer a secondary,
non-obvious resource need (e.g. food/water shortage at the destination
zone) from incomplete information. That's genuine reasoning, so it gets
a real model call.

If the API call fails or times out, we fall back to a simple rule-based
estimate rather than breaking the pipeline - this is the same "graceful
degradation" pattern discussed for field connectivity, applied here to
the AI call itself.
"""
import os
import json
import re
from anthropic import Anthropic, APIError, APITimeoutError

MODEL_NAME = os.environ.get("MODEL_NAME", "claude-sonnet-5")
TIMEOUT_SECONDS = 12

_client = None


def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        _client = Anthropic(api_key=api_key)
    return _client


PROMPT_TEMPLATE = """You are the Inference Agent inside SAATH Crisis Commander, a disaster
response coordination system. A dispatch/evacuation action has just been approved by a human
commander. Your job is to infer what SECONDARY resource need is likely to arise at the
destination zone as a result, and how confident you are in that estimate.

Situation:
- Disaster type: {disaster_type}
- Destination zone: {zone_name}
- Population being moved/affected: {population_moved}
- Destination zone's existing shelter capacity: {shelter_capacity}
- Destination zone is a designated shelter hub: {is_shelter_hub}
- Current disaster severity at destination: {severity_label}

Infer ONE likely secondary need (e.g. food_kits, water, medical_supplies) that will arise
because the destination's shelter capacity is likely far below the incoming population, and
estimate quantity and time horizon.

Respond with ONLY valid JSON, no other text, in exactly this schema:
{{"need_type": "food_kits", "estimated_quantity": 3000, "time_horizon_hours": 6, "confidence": 0.72, "reasoning": "one or two sentence explanation"}}
"""


def _extract_json(text):
    text = text.strip()
    text = re.sub(r"^```(json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def _rule_based_fallback(population_moved, shelter_capacity):
    """Used if the LLM call is unavailable/fails/times out."""
    deficit = max(population_moved - shelter_capacity, 0)
    estimated_quantity = int(deficit * 0.2)  # ~0.2 food kits per person short of shelter capacity
    return {
        "need_type": "food_kits",
        "estimated_quantity": max(estimated_quantity, 0),
        "time_horizon_hours": 6,
        "confidence": 0.4,
        "reasoning": "Fallback rule-based estimate (LLM call unavailable/failed): "
                     "quantity derived from population exceeding shelter capacity.",
        "was_fallback": True,
    }


def run_inference_agent(zone, disaster_type, population_moved, severity_label):
    client = get_client()
    inputs = {
        "disaster_type": disaster_type,
        "zone_name": zone.name,
        "population_moved": population_moved,
        "shelter_capacity": zone.shelter_capacity,
        "is_shelter_hub": zone.is_shelter_hub,
        "severity_label": severity_label,
    }

    if client is None:
        result = _rule_based_fallback(population_moved, zone.shelter_capacity)
        return result, inputs

    prompt = PROMPT_TEMPLATE.format(**inputs)
    try:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
            timeout=TIMEOUT_SECONDS,
        )
        text = "".join(block.text for block in response.content if hasattr(block, "text"))
        result = _extract_json(text)
        result["was_fallback"] = False
        return result, inputs
    except Exception as e:
     print("\n========== CLAUDE API ERROR ==========")
    print("Error type:", type(e).__name__)
    print("Error details:", str(e))
    print("======================================\n")

    result = _rule_based_fallback(
        population_moved,
        zone.shelter_capacity
    )

    result["reasoning"] = (
        f"Fallback used because Claude API failed: "
        f"{type(e).__name__}: {str(e)}"
    )

    return result, inputs
