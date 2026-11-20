"""Exact open Manhattan tour, starting at the top-left calendar cell."""
from itertools import combinations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import coo_matrix


def shortest_route(dots):
    start = (0, 0)
    points = [start, *sorted(set(dots) - {start})]
    if len(points) == 1:
        return [start]

    # Closing through a dummy vertex makes the final real vertex free.
    dummy = len(points)
    vertices = range(dummy + 1)
    edges = list(combinations(vertices, 2))
    cost = [0 if j == dummy else sum(abs(a-b) for a, b in zip(points[i], points[j]))
            for i, j in edges]
    lower = np.zeros(len(edges))
    lower[edges.index((0, dummy))] = 1
    rows = [v for edge in edges for v in edge]
    cols = [i for i in range(len(edges)) for _ in range(2)]
    degree = coo_matrix((np.ones(len(rows)), (rows, cols)),
                        shape=(len(vertices), len(edges))).tocsr()
    constraints = [LinearConstraint(degree, 2, 2)]
    while True:
        result = milp(cost, integrality=np.ones(len(edges)), bounds=Bounds(lower, 1),
                      constraints=constraints, options={"mip_rel_gap": 0})
        if not result.success:
            raise RuntimeError(result.message)
        neighbors = [[] for _ in vertices]
        for (i, j), used in zip(edges, result.x):
            if used > .5:
                neighbors[i].append(j)
                neighbors[j].append(i)
        unseen = set(vertices)
        cycles = []
        while unseen:
            cycle = []
            node = min(unseen)
            while node in unseen:
                unseen.remove(node)
                cycle.append(node)
                node = next((v for v in neighbors[node] if v in unseen), cycle[0])
            cycles.append(cycle)
        if len(cycles) == 1:
            break
        for cycle in cycles:
            group = set(cycle)
            crossing = [int((i in group) != (j in group)) for i, j in edges]
            constraints.append(LinearConstraint(crossing, 2, np.inf))

    previous, node = dummy, 0
    route = [start]
    while True:
        previous, node = node, next(v for v in neighbors[node] if v != previous)
        if node == dummy:
            break
        x, y = route[-1]
        tx, ty = points[node]
        while x != tx or y != ty:
            if x != tx:
                x += 1 if tx > x else -1
            else:
                y += 1 if ty > y else -1
            route.append((x, y))
    assert set(points) <= set(route) and len(route)-1 == round(result.mip_dual_bound)
    return route
