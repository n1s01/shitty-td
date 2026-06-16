"""Тесты для поиска пути (core/pathfinding.py).

find_path — алгоритм A*: ищет путь от старта к цели по проходимым клеткам.
smooth_path — спрямляет путь, выкидывая лишние точки.
"""

from core.grid import Grid
from core.pathfinding import find_path, smooth_path


def make_grid(cols=10, rows=10):
    return Grid(width=cols, height=rows, cols=cols, rows=rows)


def test_path_on_empty_grid_exists():
    grid = make_grid()
    path = find_path(grid, (0, 0), (5, 5))
    assert path is not None
    # Путь заканчивается в цели.
    assert path[-1] == (5, 5)


def test_path_does_not_include_start():
    # По реализации стартовая клетка в путь не попадает (came_from её не содержит).
    grid = make_grid()
    path = find_path(grid, (0, 0), (3, 0))
    assert (0, 0) not in path
    assert path == [(1, 0), (2, 0), (3, 0)]


def test_path_steps_are_adjacent():
    grid = make_grid()
    path = find_path(grid, (0, 0), (9, 9))
    prev = (0, 0)
    for cell in path:
        assert abs(cell[0] - prev[0]) <= 1
        assert abs(cell[1] - prev[1]) <= 1
        prev = cell


def test_no_path_when_target_blocked():
    grid = make_grid()
    grid.set_obstacle(5, 5)
    assert find_path(grid, (0, 0), (5, 5)) is None


def test_no_path_when_target_walled_off():
    grid = make_grid(5, 5)
    # Полностью окружаем цель (4,4)... на самом деле она в углу,
    # запираем её стеной по соседним клеткам.
    for col, row in [(3, 4), (4, 3), (3, 3)]:
        grid.set_obstacle(col, row)
    assert find_path(grid, (0, 0), (4, 4)) is None


def test_path_goes_around_obstacle():
    grid = make_grid()
    # Стена-стенка поперёк (кроме нижнего края) заставляет обходить.
    for row in range(0, 9):
        grid.set_obstacle(5, row)
    path = find_path(grid, (0, 0), (9, 0))
    assert path is not None
    # Путь не проходит через клетки-препятствия.
    for col, row in path:
        assert grid.is_walkable(col, row)


def test_path_to_self_is_empty():
    grid = make_grid()
    assert find_path(grid, (3, 3), (3, 3)) == []


def test_smooth_short_path_unchanged():
    grid = make_grid()
    assert smooth_path(grid, []) == []
    assert smooth_path(grid, [(0, 0)]) == [(0, 0)]
    assert smooth_path(grid, [(0, 0), (1, 1)]) == [(0, 0), (1, 1)]


def test_smooth_straight_line_collapses():
    grid = make_grid()
    straight = [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)]
    smoothed = smooth_path(grid, straight)
    # Прямую линию можно пройти напрямую -> остаётся начало и конец.
    assert smoothed[0] == (0, 0)
    assert smoothed[-1] == (4, 0)
    assert len(smoothed) < len(straight)


def test_smooth_keeps_endpoints_around_obstacle():
    grid = make_grid()
    grid.set_obstacle(2, 0)
    path = [(0, 0), (1, 1), (2, 1), (3, 1), (4, 0)]
    smoothed = smooth_path(grid, path)
    assert smoothed[0] == (0, 0)
    assert smoothed[-1] == (4, 0)
