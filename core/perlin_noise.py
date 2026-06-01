import math
import random


class PerlinNoise:
    """
    2D Perlin Noise (Ken Perlin, improved 2002).

    Алгоритм работает в три этапа:
      1. Permutation table — хэш-таблица из 256 случайных значений,
         дублированная до 512, чтобы избежать wrap-around ошибок.
      2. noise2d() — один октав шума:
           - Находит четыре угла клетки вокруг точки (xi, yi)
           - Для каждого угла выбирает вектор-градиент через хэш
           - Считает dot-product градиента с вектором расстояния
           - Интерполирует результаты через fade-кривую Перлина
      3. fractal_noise2d() — Fractal Brownian Motion (fBm):
           - Суммирует несколько октавов с разной частотой и амплитудой
           - Высокие октавы добавляют мелкие детали (как в природе)
    """

    # 12 градиентных векторов — равномерно распределены по направлениям
    _GRADIENTS = [
        (1, 1),
        (-1, 1),
        (1, -1),
        (-1, -1),
        (1, 0),
        (-1, 0),
        (0, 1),
        (0, -1),
        (1, 1),
        (-1, 1),
        (0, -1),
        (0, 1),
    ]

    def __init__(self, seed=None):
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)
        # Дублируем таблицу, чтобы индексировать без модуля на каждом шаге
        self._perm = perm + perm

    @staticmethod
    def _fade(t):
        # Ken Perlin's C2-непрерывная кривая: 6t^5 - 15t^4 + 10t^3
        # Обычный lerp даёт артефакты на границах клеток — эта кривая их убирает,
        # потому что её первая и вторая производные равны нулю при t=0 и t=1.
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a, b, t):
        return a + t * (b - a)

    def _grad(self, hash_val, x, y):
        """Выбираем градиент по хэшу и считаем dot-product."""
        g = self._GRADIENTS[hash_val % 12]
        return g[0] * x + g[1] * y

    def noise2d(self, x, y):
        """Один октав 2D шума Перлина. Возвращает значение примерно в [-1, 1]."""
        # Координаты клетки сетки
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255

        # Дробная часть — где внутри клетки находится точка
        xf = x - math.floor(x)
        yf = y - math.floor(y)

        # Плавные веса интерполяции
        u = self._fade(xf)
        v = self._fade(yf)

        # Хэш всех четырёх углов клетки
        aa = self._perm[self._perm[xi] + yi]
        ab = self._perm[self._perm[xi] + yi + 1]
        ba = self._perm[self._perm[xi + 1] + yi]
        bb = self._perm[self._perm[xi + 1] + yi + 1]

        # Dot-product каждого угла со своим градиентом, затем билинейная интерполяция
        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)

    def fractal_noise2d(self, x, y, octaves=4, persistence=0.5, lacunarity=2.0):
        """
        Fractal Brownian Motion: суммирует несколько октавов шума.

        persistence  — насколько уменьшается амплитуда каждого октава (0..1)
        lacunarity   — насколько увеличивается частота каждого октава (>1)
        """
        value = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_value = 0.0

        for _ in range(octaves):
            value += self.noise2d(x * frequency, y * frequency) * amplitude
            max_value += amplitude
            amplitude *= persistence
            frequency *= lacunarity

        return value / max_value

    def generate_map(
        self, cols, rows, scale=0.1, octaves=4, persistence=0.5, lacunarity=2.0
    ):
        """
        Генерирует 2D-карту шума размером cols×rows.
        Возвращает список списков со значениями в [0, 1].
        Используется для визуализации и отладки.
        """
        raw = [
            [
                self.fractal_noise2d(
                    col * scale, row * scale, octaves, persistence, lacunarity
                )
                for col in range(cols)
            ]
            for row in range(rows)
        ]

        min_val = min(v for row in raw for v in row)
        max_val = max(v for row in raw for v in row)
        val_range = max_val - min_val or 1.0

        return [[(v - min_val) / val_range for v in row] for row in raw]
