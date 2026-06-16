"""Тесты для шума Перлина (core/perlin_noise.py).

Шум Перлина используется при генерации карты (вода, влажность и т.п.).
Главное свойство — он детерминирован (один seed = одинаковый результат)
и плавный (соседние точки близки по значению).
"""

from core.perlin_noise import PerlinNoise


def test_same_seed_is_deterministic():
    a = PerlinNoise(seed=42)
    b = PerlinNoise(seed=42)
    assert a.noise2d(1.5, 2.5) == b.noise2d(1.5, 2.5)


def test_different_seeds_differ():
    a = PerlinNoise(seed=1)
    b = PerlinNoise(seed=2)
    # Хотя бы в одной точке значения должны отличаться.
    points = [(x * 0.3, y * 0.3) for x in range(5) for y in range(5)]
    assert any(a.noise2d(x, y) != b.noise2d(x, y) for x, y in points)


def test_noise_at_integers_is_zero():
    # Классическое свойство Перлина: в узлах решётки шум равен 0.
    noise = PerlinNoise(seed=7)
    assert abs(noise.noise2d(3, 5)) < 1e-9


def test_noise_in_expected_range():
    noise = PerlinNoise(seed=123)
    for x in range(20):
        for y in range(20):
            v = noise.noise2d(x * 0.37, y * 0.51)
            # 2D-шум Перлина лежит примерно в [-1, 1].
            assert -1.5 < v < 1.5


def test_fractal_noise_is_smooth():
    noise = PerlinNoise(seed=5)
    a = noise.fractal_noise2d(2.0, 2.0)
    b = noise.fractal_noise2d(2.001, 2.0)
    # Очень близкие точки -> очень близкие значения.
    assert abs(a - b) < 0.05


def test_generate_map_dimensions_and_normalization():
    noise = PerlinNoise(seed=9)
    cols, rows = 12, 8
    grid = noise.generate_map(cols, rows, scale=0.15)
    assert len(grid) == rows
    assert all(len(row) == cols for row in grid)
    # Карта нормализована в диапазон [0, 1].
    flat = [v for row in grid for v in row]
    assert min(flat) >= 0.0
    assert max(flat) <= 1.0


def test_generate_map_is_deterministic():
    g1 = PerlinNoise(seed=99).generate_map(6, 6, scale=0.2)
    g2 = PerlinNoise(seed=99).generate_map(6, 6, scale=0.2)
    assert g1 == g2
