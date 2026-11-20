"""Plan patrols on the same clock as the optimal pellet route."""
from functools import lru_cache
from random import Random


@lru_cache(maxsize=8192)
def clearance(dx, dy, vx, vy):
    """Minimum squared distance during one pair of simultaneous linear moves."""
    speed = vx*vx + vy*vy
    t = max(0, min(1, -(dx*vx + dy*vy)/speed)) if speed else 0
    return (dx+t*vx)**2 + (dy+t*vy)**2


def patrol(player, occupied, cells, lane, lag):
    # Dynamic programming allows a ghost to anticipate a corner or reverse turn.
    moves = [(1,0), (-1,0), (0,1), (0,-1)]
    rng = Random(731 + lag)
    # A changing waypoint gives each chase a drift lasting several beats.
    next_change = 1
    min_squared = [1] * len(occupied)
    safe = {c: 0 for c in cells if all((c[0]-p[0][0])**2+(c[1]-p[0][1])**2 >= limit
                                        for p, limit in zip(occupied, min_squared))}
    history = []
    for tick in range(1, len(player)):
        if tick == next_change:
            delay = rng.randint(lag-2, lag+2)
            drift_x = rng.choice([-1, 0, 1])
            drift_y = rng.randint(-2, 2) + (1 if lane > 0 else -1)
            next_change += rng.randint(6, 12)
        target_x, target_y = player[max(0, tick-delay)]
        target_x += drift_x
        target_y = max(0, min(6, target_y + drift_y))
        guards = [(p[tick-1], p[tick]) for p in occupied]
        costs, parents = {}, {}
        for (x,y), cost in safe.items():
            for vx,vy in moves:
                cell = (x+vx, y+vy)
                if cell not in cells:
                    continue
                score = cost + abs(cell[0]-target_x) + abs(cell[1]-target_y)
                # Avoid pacing back and forth while the player turns.
                if history and history[-1][x,y] == cell:
                    score += 5
                if score >= costs.get(cell, float("inf")):
                    continue
                if any(clearance(x-a, y-b, vx-(c-a), vy-(d-b)) < limit
                       for ((a,b),(c,d)), limit in zip(guards, min_squared)):
                    continue
                costs[cell], parents[cell] = score, (x,y)
        history.append(parents)
        safe = costs
    cell = min(safe, key=safe.get)
    path = [cell]
    for parents in reversed(history):
        cell = parents[cell]
        path.append(cell)
    return path[::-1]
