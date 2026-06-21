"""Поиск пути по сетке (A*) и сглаживание маршрута."""

import heapq
import math


def find_path(grid, start, end):
    """Ищет кратчайший путь между клетками алгоритмом A*.

    Args:
        grid: сетка игрового поля (объект Grid).
        start: начальная клетка в виде (col, row).
        end: целевая клетка в виде (col, row).

    Returns:
        Список клеток пути (без стартовой) или None, если путь не
        найден либо цель непроходима.
    """
    if not grid.is_walkable(end[0], end[1]):
        return None

    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0.0}

    while open_set:
        _, current = heapq.heappop(open_set)

        if current == end:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path

        for neighbor in grid.get_neighbors(current[0], current[1]):
            col_offset = neighbor[0] - current[0]
            row_offset = neighbor[1] - current[1]
            move_cost = 1.4 if col_offset != 0 and row_offset != 0 else 1.0
            tentative_g = g_score[current] + move_cost

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                heuristic = math.hypot(end[0] - neighbor[0], end[1] - neighbor[1])
                heapq.heappush(open_set, (tentative_g + heuristic, neighbor))

    return None


def smooth_path(grid, path):
    """Убирает лишние точки пути, спрямляя прямые участки.

    Идёт по маршруту и заменяет цепочки клеток на самую дальнюю клетку,
    до которой есть прямая видимость по проходимым клеткам.

    Args:
        grid: сетка игрового поля (объект Grid).
        path: исходный список клеток (col, row).

    Returns:
        Сглаженный список клеток. Если в пути не больше двух точек,
        возвращается он же без изменений.
    """
    if len(path) <= 2:
        return path

    smoothed = [path[0]]
    current_index = 0

    while current_index < len(path) - 1:
        furthest_visible = current_index + 1
        for check_index in range(current_index + 2, len(path)):
            if _line_walkable(grid, path[current_index], path[check_index]):
                furthest_visible = check_index
        smoothed.append(path[furthest_visible])
        current_index = furthest_visible

    return smoothed


def _line_walkable(grid, start, end):
    """Проверяет прямую видимость между клетками (алгоритм Брезенхэма).

    Args:
        grid: сетка игрового поля (объект Grid).
        start: начальная клетка (col, row).
        end: конечная клетка (col, row).

    Returns:
        True, если все клетки на прямой между start и end проходимы,
        иначе False.
    """
    col_start, row_start = start
    col_end, row_end = end
    col_distance = abs(col_end - col_start)
    row_distance = abs(row_end - row_start)
    col_step = 1 if col_end > col_start else -1
    row_step = 1 if row_end > row_start else -1
    error = col_distance - row_distance

    while True:
        if not grid.is_walkable(col_start, row_start):
            return False
        if col_start == col_end and row_start == row_end:
            return True
        double_error = 2 * error
        if double_error > -row_distance:
            error -= row_distance
            col_start += col_step
        if double_error < col_distance:
            error += col_distance
            row_start += row_step
