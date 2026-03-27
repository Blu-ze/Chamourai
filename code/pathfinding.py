import heapq
import math

CELL_SIZE = 32
MOB_HALF  = 1

class _Node:
    __slots__ = ('x', 'y', 'g', 'f', 'parent')
    def __init__(self, x, y, g, h, parent=None):
        self.x = x; self.y = y; self.g = g
        self.f = g + h; self.parent = parent
    def __lt__(self, other):
        return self.f < other.f

def _heuristic(ax, ay, bx, by):
    return max(abs(ax - bx), abs(ay - by))

def world_to_grid(wx, wy):
    try:
        return int(wx) // CELL_SIZE, int(wy) // CELL_SIZE
    except (ValueError, OverflowError):
        return 0, 0

def grid_to_world(gx, gy):
    return gx * CELL_SIZE + CELL_SIZE // 2, gy * CELL_SIZE + CELL_SIZE // 2

def build_collision_set(collisions):
    blocked = set()
    for rect in collisions:
        if rect.width <= 0 or rect.height <= 0:
            continue
        x0 = rect.left  // CELL_SIZE - MOB_HALF
        x1 = math.ceil(rect.right  / CELL_SIZE) + MOB_HALF
        y0 = rect.top   // CELL_SIZE - MOB_HALF
        y1 = math.ceil(rect.bottom / CELL_SIZE) + MOB_HALF
        for gx in range(x0, x1 + 1):
            for gy in range(y0, y1 + 1):
                blocked.add((gx, gy))
    return blocked

_NEIGHBORS = [
    ( 1,  0, 1.0), (-1,  0, 1.0), ( 0,  1, 1.0), ( 0, -1, 1.0),
    ( 1,  1, 1.414), (-1,  1, 1.414), ( 1, -1, 1.414), (-1, -1, 1.414),
]

def astar(start_world, goal_world, blocked_cells, max_iterations=4000):
    try:
        sx, sy = world_to_grid(*start_world)
        gx, gy = world_to_grid(*goal_world)
    except Exception:
        return []

    if (sx, sy) == (gx, gy):
        return []

    for start_blocked, coord in [(True, 'start'), (False, 'goal')]:
        cx, cy = (sx, sy) if coord == 'start' else (gx, gy)
        if (cx, cy) in blocked_cells:
            found = False
            for radius in range(1, 5):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        cand = (cx + dx, cy + dy)
                        if cand not in blocked_cells:
                            if coord == 'start':
                                sx, sy = cand
                            else:
                                gx, gy = cand
                            found = True
                            break
                    if found: break
                if found: break
            else:
                return []

    start_node = _Node(sx, sy, 0, _heuristic(sx, sy, gx, gy))
    open_list  = [start_node]
    open_dict  = {(sx, sy): 0.0}
    closed_set = set()

    iterations = 0
    while open_list and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_list)
        key = (current.x, current.y)
        if key in closed_set:
            continue
        closed_set.add(key)

        if current.x == gx and current.y == gy:
            path = []
            node = current
            while node:
                path.append(grid_to_world(node.x, node.y))
                node = node.parent
            path.reverse()
            return path

        for dx, dy, cost in _NEIGHBORS:
            nx, ny = current.x + dx, current.y + dy
            nkey = (nx, ny)
            if nkey in closed_set or nkey in blocked_cells:
                continue
            ng = current.g + cost
            if ng < open_dict.get(nkey, float('inf')):
                open_dict[nkey] = ng
                heapq.heappush(open_list, _Node(nx, ny, ng, _heuristic(nx, ny, gx, gy), current))

    return []