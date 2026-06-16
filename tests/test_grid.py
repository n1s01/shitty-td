"""Тесты для сетки (core/grid.py).

Сетка переводит мировые координаты (пиксели) в координаты клеток и обратно,
хранит препятствия и умеет находить проходимых соседей клетки.
"""

import pytest

from core.grid import Grid


@pytest.fixture
def grid():
    # Поле 100x100 пикселей, разбитое на 10x10 клеток -> клетка 10x10 пикселей.
    return Grid(width=100, height=100, cols=10, rows=10)


def test_cell_size(grid):
    assert grid.cell_w == 10
    assert grid.cell_h == 10


def test_world_to_grid_basic(grid):
    # Точка (25, 35) попадает в клетку (2, 3).
    assert grid.world_to_grid(25, 35) == (2, 3)


def test_world_to_grid_clamps_inside_bounds(grid):
    # Координаты за пределами поля прижимаются к крайним клеткам.
    assert grid.world_to_grid(-50, -50) == (0, 0)
    assert grid.world_to_grid(9999, 9999) == (9, 9)


def test_grid_to_world_returns_cell_center(grid):
    # Центр клетки (0, 0) находится в точке (5, 5).
    assert grid.grid_to_world(0, 0) == (5, 5)
    assert grid.grid_to_world(2, 3) == (25, 35)


def test_roundtrip_world_grid_world(grid):
    # Перевод в клетку и обратно даёт центр той же клетки.
    col, row = grid.world_to_grid(25, 35)
    assert grid.world_to_grid(*grid.grid_to_world(col, row)) == (col, row)


def test_new_grid_is_fully_walkable(grid):
    assert grid.is_walkable(0, 0)
    assert grid.is_walkable(9, 9)


def test_out_of_bounds_not_walkable(grid):
    assert not grid.is_walkable(-1, 0)
    assert not grid.is_walkable(0, -1)
    assert not grid.is_walkable(10, 0)
    assert not grid.is_walkable(0, 10)


def test_set_and_remove_obstacle(grid):
    grid.set_obstacle(5, 5)
    assert not grid.is_walkable(5, 5)
    grid.remove_obstacle(5, 5)
    assert grid.is_walkable(5, 5)


def test_set_obstacle_out_of_bounds_is_ignored(grid):
    # Не должно падать с ошибкой, просто ничего не делает.
    grid.set_obstacle(-1, -1)
    grid.set_obstacle(100, 100)


def test_neighbors_in_center_count(grid):
    # У клетки в центре поля 8 соседей (вкл. диагонали).
    assert len(grid.get_neighbors(5, 5)) == 8


def test_neighbors_in_corner_count(grid):
    # У угловой клетки только 3 соседа.
    assert len(grid.get_neighbors(0, 0)) == 3


def test_neighbors_skip_obstacles(grid):
    grid.set_obstacle(4, 5)
    grid.set_obstacle(6, 5)
    neighbors = grid.get_neighbors(5, 5)
    assert (4, 5) not in neighbors
    assert (6, 5) not in neighbors
    assert len(neighbors) == 6
