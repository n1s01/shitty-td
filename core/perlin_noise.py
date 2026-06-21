"""Шум Перлина для процедурной генерации карт высот."""

import math
import random


class PerlinNoise:
    """Генератор двумерного шума Перлина.

    По заданному seed строит таблицу перестановок и вычисляет гладкий
    псевдослучайный шум, удобный для генерации ландшафта.
    """

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
        """Инициализирует генератор таблицей перестановок.

        Args:
            seed: зерно генератора случайных чисел. При одинаковом seed
                карта получается воспроизводимой.
        """
        rng = random.Random(seed)
        perm = list(range(256))
        rng.shuffle(perm)

        self._perm = perm + perm

    @staticmethod
    def _fade(t):
        """Сглаживающая функция Перлина 6t^5 - 15t^4 + 10t^3.

        Args:
            t: значение в диапазоне [0, 1].

        Returns:
            Сглаженное значение для плавной интерполяции.
        """
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a, b, t):
        """Линейно интерполирует между двумя значениями.

        Args:
            a: значение при t = 0.
            b: значение при t = 1.
            t: коэффициент интерполяции [0, 1].

        Returns:
            Промежуточное значение между a и b.
        """
        return a + t * (b - a)

    def _grad(self, hash_val, x, y):
        """Скалярное произведение точки с псевдослучайным градиентом.

        Args:
            hash_val: хеш узла сетки, выбирающий градиент.
            x: смещение по горизонтали относительно узла.
            y: смещение по вертикали относительно узла.

        Returns:
            Вклад градиента в значение шума.
        """
        g = self._GRADIENTS[hash_val % 12]
        return g[0] * x + g[1] * y

    def noise2d(self, x, y):
        """Вычисляет значение шума Перлина в точке.

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.

        Returns:
            Значение шума примерно в диапазоне [-1, 1].
        """
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255

        xf = x - math.floor(x)
        yf = y - math.floor(y)

        u = self._fade(xf)
        v = self._fade(yf)

        aa = self._perm[self._perm[xi] + yi]
        ab = self._perm[self._perm[xi] + yi + 1]
        ba = self._perm[self._perm[xi + 1] + yi]
        bb = self._perm[self._perm[xi + 1] + yi + 1]

        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)

    def fractal_noise2d(self, x, y, octaves=4, persistence=0.5, lacunarity=2.0):
        """Складывает несколько октав шума для большей детализации.

        Args:
            x: координата по горизонтали.
            y: координата по вертикали.
            octaves: число складываемых слоёв шума.
            persistence: во сколько раз уменьшается амплитуда каждой
                следующей октавы.
            lacunarity: во сколько раз растёт частота каждой следующей
                октавы.

        Returns:
            Нормированное значение шума примерно в диапазоне [-1, 1].
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
        """Строит карту высот заданного размера на основе шума.

        Значения карты нормируются в диапазон [0, 1].

        Args:
            cols: число колонок карты.
            rows: число строк карты.
            scale: масштаб шума (меньше - крупнее формы рельефа).
            octaves: число октав фрактального шума.
            persistence: спад амплитуды по октавам.
            lacunarity: рост частоты по октавам.

        Returns:
            Двумерный список (rows x cols) значений высоты в [0, 1].
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
