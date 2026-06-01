import math
import random


class PerlinNoise:
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

        self._perm = perm + perm

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a, b, t):
        return a + t * (b - a)

    def _grad(self, hash_val, x, y):
        g = self._GRADIENTS[hash_val % 12]
        return g[0] * x + g[1] * y

    def noise2d(self, x, y):
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
