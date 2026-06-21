"""Процедурная генерация карты: вода, берег, декор и препятствия."""

import math
import random

from config import GAME_CONFIG
from core.models import Obstacle
from core.perlin_noise import PerlinNoise

GRASS = 0
WATER = 1
SHORE = 2


class GeneratedMap:
    """Готовая карта: биомы клеток, декор и препятствия."""

    def __init__(self, cols, rows, tile_size, biomes, decor, obstacles):
        """Сохраняет результат генерации карты.

        Args:
            cols: число колонок карты.
            rows: число строк карты.
            tile_size: размер тайла в пикселях.
            biomes: двумерный список биомов (GRASS/WATER/SHORE).
            decor: список декоративных объектов.
            obstacles: список препятствий (объекты Obstacle).
        """
        self.cols = cols
        self.rows = rows
        self.tile_size = tile_size
        self.biomes = biomes
        self.decor = decor
        self.obstacles = obstacles


class MapGenerator:
    """Строит карту вокруг башни на основе шума Перлина.

    Генерирует водоёмы, гарантирует проходимость до башни, добавляет
    берега, декор и препятствия, оставляя безопасную зону у башни.
    """

    def __init__(self, width, height, tower_x, tower_y):
        """Готовит параметры генерации под размер поля и башню.

        Args:
            width: ширина поля в пикселях.
            height: высота поля в пикселях.
            tower_x: координата башни по горизонтали.
            tower_y: координата башни по вертикали.
        """
        self.width = width
        self.height = height
        self.tower_x = tower_x
        self.tower_y = tower_y

        self.tile_size = GAME_CONFIG["map_tile_size"]
        self.cols = math.ceil(width / self.tile_size)
        self.rows = math.ceil(height / self.tile_size)
        self.safe_radius = (
            max(width, height) * GAME_CONFIG["map_obstacle_safe_radius_factor"]
        )

        self._base_seed = random.randint(0, 2**31 - 1)

    def generate(self):
        """Генерирует карту, перебирая попытки до приемлемого водного покрытия.

        Returns:
            Объект GeneratedMap с биомами, декором и препятствиями.
        """
        attempts = GAME_CONFIG["map_gen_attempts"]
        reject = GAME_CONFIG["water_reject_fraction"]

        best = None
        for attempt in range(attempts):
            seed = self._base_seed + attempt
            biomes = self._build_water(seed)
            self._enforce_connectivity(biomes)
            self._keep_largest_lake(biomes)
            fraction = self._water_fraction(biomes)
            best = (biomes, seed)
            if fraction <= reject:
                break

        biomes, seed = best
        self._derive_shore(biomes)
        rng = random.Random(seed)
        decor = self._place_decor(biomes, seed, rng)
        obstacles = self._place_obstacles(biomes, rng)
        return GeneratedMap(
            self.cols, self.rows, self.tile_size, biomes, decor, obstacles
        )

    def _build_water(self, seed):
        """Расставляет воду по карте по порогу значения шума.

        Args:
            seed: зерно генератора шума.

        Returns:
            Двумерный список биомов с водой (WATER) и травой (GRASS).
        """
        noise = PerlinNoise(seed)
        scale = GAME_CONFIG["water_noise_scale"]
        octaves = GAME_CONFIG["noise_octaves"]
        persistence = GAME_CONFIG["noise_persistence"]
        lacunarity = GAME_CONFIG["noise_lacunarity"]

        values = [[0.0] * self.cols for _ in range(self.rows)]
        candidates = []
        for row in range(self.rows):
            for col in range(self.cols):
                v = noise.fractal_noise2d(
                    col * scale, row * scale, octaves, persistence, lacunarity
                )
                values[row][col] = v
                if not self._is_safe_tile(col, row):
                    candidates.append(v)

        candidates.sort()
        target = GAME_CONFIG["water_target_fraction"]
        idx = min(len(candidates) - 1, int(len(candidates) * target))
        threshold = candidates[idx] if candidates else 0.0

        biomes = [[GRASS] * self.cols for _ in range(self.rows)]
        for row in range(self.rows):
            for col in range(self.cols):
                if self._is_border_tile(col, row):
                    continue
                if self._is_safe_tile(col, row):
                    continue
                if values[row][col] <= threshold:
                    biomes[row][col] = WATER
        return biomes

    def _enforce_connectivity(self, biomes):
        """Заливает водой участки суши, недостижимые от башни.

        Args:
            biomes: двумерный список биомов (изменяется на месте).
        """
        tcol, trow = self._tower_tile()
        reachable = [[False] * self.cols for _ in range(self.rows)]
        stack = [(tcol, trow)]
        reachable[trow][tcol] = True
        while stack:
            col, row = stack.pop()
            for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nc, nr = col + dc, row + dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    if not reachable[nr][nc] and biomes[nr][nc] != WATER:
                        reachable[nr][nc] = True
                        stack.append((nc, nr))

        for row in range(self.rows):
            for col in range(self.cols):
                if biomes[row][col] != WATER and not reachable[row][col]:
                    biomes[row][col] = WATER

    def _keep_largest_lake(self, biomes):
        """Оставляет только самый большой водоём, остальные - травой.

        Args:
            biomes: двумерный список биомов (изменяется на месте).
        """
        seen = [[False] * self.cols for _ in range(self.rows)]
        components = []
        for row in range(self.rows):
            for col in range(self.cols):
                if biomes[row][col] != WATER or seen[row][col]:
                    continue
                comp = []
                stack = [(col, row)]
                seen[row][col] = True
                while stack:
                    c, r = stack.pop()
                    comp.append((c, r))
                    for dc, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nc, nr = c + dc, r + dr
                        if 0 <= nc < self.cols and 0 <= nr < self.rows:
                            if not seen[nr][nc] and biomes[nr][nc] == WATER:
                                seen[nr][nc] = True
                                stack.append((nc, nr))
                components.append(comp)

        if len(components) <= 1:
            return
        largest = max(components, key=len)
        for comp in components:
            if comp is largest:
                continue
            for c, r in comp:
                biomes[r][c] = GRASS

    def _water_fraction(self, biomes):
        """Возвращает долю клеток, занятых водой.

        Args:
            biomes: двумерный список биомов.

        Returns:
            Доля воды от 0.0 до 1.0.
        """
        total = self.cols * self.rows
        water = sum(row.count(WATER) for row in biomes)
        return water / total if total else 0.0

    def _derive_shore(self, biomes):
        """Помечает клетки травы у воды как берег (SHORE).

        Args:
            biomes: двумерный список биомов (изменяется на месте).
        """
        shore = []
        for row in range(self.rows):
            for col in range(self.cols):
                if biomes[row][col] != GRASS:
                    continue
                if self._touches_water(biomes, col, row):
                    shore.append((col, row))
        for col, row in shore:
            biomes[row][col] = SHORE

    def _touches_water(self, biomes, col, row):
        """Проверяет, граничит ли клетка с водой по 8 направлениям.

        Args:
            biomes: двумерный список биомов.
            col: номер колонки клетки.
            row: номер строки клетки.

        Returns:
            True, если рядом есть вода, иначе False.
        """
        for dc in (-1, 0, 1):
            for dr in (-1, 0, 1):
                if dc == 0 and dr == 0:
                    continue
                nc, nr = col + dc, row + dr
                if 0 <= nc < self.cols and 0 <= nr < self.rows:
                    if biomes[nr][nc] == WATER:
                        return True
        return False

    def _place_decor(self, biomes, seed, rng):
        """Расставляет декор по биомам с учётом карты влажности.

        Args:
            biomes: двумерный список биомов.
            seed: зерно для шума влажности.
            rng: генератор случайных чисел.

        Returns:
            Список декоративных объектов в виде словарей.
        """
        decor = []
        ts = self.tile_size

        moist = PerlinNoise(seed + 9999)
        mscale = GAME_CONFIG["moisture_noise_scale"]
        mvals = [
            [
                moist.fractal_noise2d(col * mscale, row * mscale)
                for col in range(self.cols)
            ]
            for row in range(self.rows)
        ]
        flat = [v for r in mvals for v in r]
        lo, hi = min(flat), max(flat)
        span = (hi - lo) or 1.0

        flower_assets = ["decor/flowers_blue.png", "decor/flowers_purple.png"]
        scatter_assets = [
            "decor/grass_tuft_1.png",
            "decor/grass_tuft_2.png",
            "decor/clover.png",
            "decor/mushroom_red.png",
            "decor/mushroom_brown.png",
            "decor/fern.png",
            "decor/pebbles.png",
        ]
        lily_assets = ["decor/lily_pad_1.png", "decor/lily_pad_2.png"]
        reed_assets = ["decor/reeds_1.png", "decor/reeds_2.png"]

        flower_density = GAME_CONFIG["flower_density"]
        flower_threshold = GAME_CONFIG["flower_threshold"]
        scatter_density = GAME_CONFIG["scatter_density"]
        lily_density = GAME_CONFIG["lily_density"]
        reed_density = GAME_CONFIG["reed_density"]

        for row in range(self.rows):
            for col in range(self.cols):
                biome = biomes[row][col]
                cx = col * ts + ts / 2
                cy = row * ts + ts / 2

                if biome == WATER:
                    if rng.random() < lily_density:
                        decor.append(
                            self._decor_item(rng.choice(lily_assets), cx, cy, rng, ts)
                        )
                elif biome == SHORE:
                    if rng.random() < reed_density:
                        decor.append(
                            self._decor_item(rng.choice(reed_assets), cx, cy, rng, ts)
                        )
                    elif rng.random() < 0.4:
                        decor.append(
                            self._decor_item("decor/pebbles.png", cx, cy, rng, ts)
                        )
                else:
                    if self._is_safe_world(cx, cy):
                        continue
                    moisture = (mvals[row][col] - lo) / span
                    if moisture > flower_threshold and rng.random() < flower_density:
                        decor.append(
                            self._decor_item(rng.choice(flower_assets), cx, cy, rng, ts)
                        )
                    elif rng.random() < scatter_density:
                        decor.append(
                            self._decor_item(
                                rng.choice(scatter_assets), cx, cy, rng, ts
                            )
                        )
        return decor

    def _decor_item(self, asset, cx, cy, rng, ts):
        """Создаёт декоративный объект со случайным смещением.

        Args:
            asset: путь к изображению декора.
            cx: координата центра клетки по горизонтали.
            cy: координата центра клетки по вертикали.
            rng: генератор случайных чисел.
            ts: размер тайла (определяет величину смещения).

        Returns:
            Словарь с ключами "asset", "x" и "y".
        """
        jitter = ts * 0.3
        return {
            "asset": asset,
            "x": cx + rng.uniform(-jitter, jitter),
            "y": cy + rng.uniform(-jitter, jitter),
        }

    def _place_obstacles(self, biomes, rng):
        """Раскидывает препятствия по суше вне безопасной зоны.

        Args:
            biomes: двумерный список биомов.
            rng: генератор случайных чисел.

        Returns:
            Список препятствий (объекты Obstacle).
        """
        specs = GAME_CONFIG["land_obstacles"]
        target = GAME_CONFIG["land_obstacle_count"]
        min_dist = GAME_CONFIG["land_obstacle_min_dist"]
        obstacles = []
        attempts = 0
        while len(obstacles) < target and attempts < target * 200:
            attempts += 1
            spec = rng.choice(specs)
            w, h = spec["size"]
            x = rng.uniform(w, self.width - w)
            y = rng.uniform(h, self.height - h)
            if self._is_safe_world(x, y):
                continue
            if self._biome_at(biomes, x, y) != GRASS:
                continue
            if any(math.hypot(x - o.x, y - o.y) < min_dist for o in obstacles):
                continue
            obstacles.append(
                Obstacle(
                    x=x,
                    y=y,
                    width=w,
                    height=h,
                    asset=spec["asset"],
                    solid=spec.get("solid", True),
                )
            )
        return obstacles

    def _biome_at(self, biomes, x, y):
        """Возвращает биом клетки по координатам мира.

        Args:
            biomes: двумерный список биомов.
            x: координата по горизонтали в пикселях.
            y: координата по вертикали в пикселях.

        Returns:
            Код биома (GRASS, WATER или SHORE).
        """
        col = int(x / self.tile_size)
        row = int(y / self.tile_size)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return biomes[row][col]

    def _tower_tile(self):
        """Возвращает клетку (col, row), в которой стоит башня.

        Returns:
            Кортеж (col, row), обрезанный до границ карты.
        """
        col = int(self.tower_x / self.tile_size)
        row = int(self.tower_y / self.tile_size)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    def _is_border_tile(self, col, row):
        """Проверяет, лежит ли клетка на краю карты.

        Args:
            col: номер колонки.
            row: номер строки.

        Returns:
            True, если клетка на границе карты, иначе False.
        """
        return col == 0 or row == 0 or col == self.cols - 1 or row == self.rows - 1

    def _is_safe_tile(self, col, row):
        """Проверяет, попадает ли клетка в безопасную зону у башни.

        Args:
            col: номер колонки.
            row: номер строки.

        Returns:
            True, если центр клетки в радиусе безопасной зоны.
        """
        cx = col * self.tile_size + self.tile_size / 2
        cy = row * self.tile_size + self.tile_size / 2
        return self._is_safe_world(cx, cy)

    def _is_safe_world(self, x, y):
        """Проверяет, попадает ли точка мира в безопасную зону у башни.

        Args:
            x: координата по горизонтали в пикселях.
            y: координата по вертикали в пикселях.

        Returns:
            True, если точка ближе safe_radius к башне, иначе False.
        """
        return math.hypot(x - self.tower_x, y - self.tower_y) < self.safe_radius
