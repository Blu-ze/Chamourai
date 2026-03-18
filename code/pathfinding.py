"""
pathfinding.py — A* sur grille pour les ennemis de Chamourai.

Principes clés :
  - CELL_SIZE=32  → résolution fine, compatible avec les petits rects de collision
  - Les rects de collision sont dilatés d'une demi-largeur de mob (MOB_HALF = 1 cellule)
    pour que le centre du mob ne longe jamais le bord d'un mur.
  - max_iterations=4000 couvre les trajets les plus longs de la map (≈4736×4480 px).
  - astar() ne lève jamais d'exception et renvoie toujours une liste (vide si échec).
"""

import heapq
import math

CELL_SIZE    = 32   # px par cellule de grille
MOB_HALF     = 1    # demi-largeur du mob en cellules → marge autour des collisions


# ─── Nœud A* ──────────────────────────────────────────────────────────────────

class _Node:
    __slots__ = ('x', 'y', 'g', 'f', 'parent')

    def __init__(self, x, y, g, h, parent=None):
        self.x = x
        self.y = y
        self.g = g
        self.f = g + h
        self.parent = parent

    def __lt__(self, other):
        return self.f < other.f


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _heuristic(ax, ay, bx, by):
    # Distance de Tchebychev (optimale pour déplacements 8-dir)
    return max(abs(ax - bx), abs(ay - by))


def world_to_grid(wx, wy):
    try:
        return int(wx) // CELL_SIZE, int(wy) // CELL_SIZE
    except (ValueError, OverflowError):
        return 0, 0


def grid_to_world(gx, gy):
    return gx * CELL_SIZE + CELL_SIZE // 2, gy * CELL_SIZE + CELL_SIZE // 2


# ─── Construction de la grille bloquée ────────────────────────────────────────

def build_collision_set(collisions):
    """
    Convertit la liste de pygame.Rect de collision en un ensemble de cellules
    bloquées, dilatées de MOB_HALF cellule(s) pour tenir compte de la taille du mob.
    """
    blocked = set()
    for rect in collisions:
        if rect.width <= 0 or rect.height <= 0:
            continue
        # Cellules couvertes par le rect, avec marge
        x0 = rect.left  // CELL_SIZE - MOB_HALF
        x1 = math.ceil(rect.right  / CELL_SIZE) + MOB_HALF
        y0 = rect.top   // CELL_SIZE - MOB_HALF
        y1 = math.ceil(rect.bottom / CELL_SIZE) + MOB_HALF
        for gx in range(x0, x1 + 1):
            for gy in range(y0, y1 + 1):
                blocked.add((gx, gy))
    return blocked


# ─── A* principal ─────────────────────────────────────────────────────────────

_NEIGHBORS = [
    ( 1,  0, 1.0),  (-1,  0, 1.0),  ( 0,  1, 1.0),  ( 0, -1, 1.0),
    ( 1,  1, 1.414),(-1,  1, 1.414),( 1, -1, 1.414),(-1, -1, 1.414),
]

def astar(start_world, goal_world, blocked_cells, max_iterations=4000):
    """
    Renvoie la liste des positions monde (centres de cellules) formant
    le chemin de start à goal, ou [] si aucun chemin n'est trouvé.
    Ne lève jamais d'exception.
    """
    try:
        sx, sy = world_to_grid(*start_world)
        gx, gy = world_to_grid(*goal_world)
    except Exception:
        return []

    # Cas trivial
    if (sx, sy) == (gx, gy):
        return []

    # Si le départ est bloqué, chercher la cellule libre la plus proche
    if (sx, sy) in blocked_cells:
        found_start = False
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    cand = (sx + dx, sy + dy)
                    if cand not in blocked_cells:
                        sx, sy = cand
                        found_start = True
                        break
                if found_start:
                    break
            if found_start:
                break
        else:
            return []

    # Si la cible est bloquée, chercher la cellule libre la plus proche
    if (gx, gy) in blocked_cells:
        found_goal = False
        for radius in range(1, 5):
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    cand = (gx + dx, gy + dy)
                    if cand not in blocked_cells:
                        gx, gy = cand
                        found_goal = True
                        break
                if found_goal:
                    break
            if found_goal:
                break
        else:
            return []

    # A*
    start_node = _Node(sx, sy, 0, _heuristic(sx, sy, gx, gy))
    open_list  = [start_node]
    open_dict  = {(sx, sy): 0.0}   # key → meilleur g connu
    closed_set = set()

    iterations = 0
    while open_list and iterations < max_iterations:
        iterations += 1
        current = heapq.heappop(open_list)
        key = (current.x, current.y)

        if key in closed_set:
            continue
        closed_set.add(key)

        # Cible atteinte → reconstruction
        if current.x == gx and current.y == gy:
            path = []
            node = current
            while node:
                path.append(grid_to_world(node.x, node.y))
                node = node.parent
            path.reverse()
            return path

        for dx, dy, cost in _NEIGHBORS:
            nx, ny  = current.x + dx, current.y + dy
            nkey    = (nx, ny)
            if nkey in closed_set or nkey in blocked_cells:
                continue
            ng = current.g + cost
            if ng < open_dict.get(nkey, float('inf')):
                open_dict[nkey] = ng
                heapq.heappush(open_list, _Node(nx, ny, ng, _heuristic(nx, ny, gx, gy), current))

    return []   # Pas de chemin trouvé
