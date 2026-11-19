"""
Routing Agent - RULE-BASED (simple BFS over the road graph).

Checks whether a path exists from the resource HQ zone to a proposed
dispatch's target zone, avoiding blocked roads. Small zone count (8)
means BFS is more than sufficient - no need for real pathfinding libs.
"""
from collections import deque
from ..models import Road
from ..seed_data import HQ_ZONE_ID


def build_graph(db):
    roads = db.query(Road).all()
    graph = {}
    for r in roads:
        if r.status != "open":
            continue
        graph.setdefault(r.zone_a_id, []).append(r.zone_b_id)
        graph.setdefault(r.zone_b_id, []).append(r.zone_a_id)
    return graph


def bfs_path_exists(graph, start, target):
    if start == target:
        return True, 0
    visited = {start}
    q = deque([(start, 0)])
    while q:
        node, hops = q.popleft()
        for neighbor in graph.get(node, []):
            if neighbor == target:
                return True, hops + 1
            if neighbor not in visited:
                visited.add(neighbor)
                q.append((neighbor, hops + 1))
    return False, None


def run_routing_agent(db, proposals):
    graph = build_graph(db)
    from ..models import Action
    results = []
    for p in proposals:
        valid, hops = bfs_path_exists(graph, HQ_ZONE_ID, p["zone_id"])
        eta = (hops or 0) * 15 + 10 if valid else None  # ~15 min per hop + 10 min mobilization

        action = db.get(Action, p["action_id"])
        if action:
            action.route_valid = valid
            action.eta_minutes = eta
        results.append({**p, "route_valid": valid, "eta_minutes": eta})
    db.commit()
    return results


def recheck_all_pending_routes(db):
    """Called after a road_block/road_clear event to re-validate existing pending actions."""
    from ..models import Action
    graph = build_graph(db)
    pending = db.query(Action).filter(Action.status == "pending").all()
    changed = []
    for action in pending:
        valid, hops = bfs_path_exists(graph, HQ_ZONE_ID, action.target_zone_id)
        eta = (hops or 0) * 15 + 10 if valid else None
        if action.route_valid != valid:
            changed.append(action.id)
        action.route_valid = valid
        action.eta_minutes = eta
    db.commit()
    return changed
