import math
import random

from config import GAME_CONFIG
from core.models import Obstacle
from core.perlin_noise import PerlinNoise

GRASS = 0
WATER = 1
SHORE = 2


class GeneratedMap:
    def __init__(self, cols, rows, tile_size, biomes, decor, obstacles):
        self.cols = cols
        self.rows = rows
        self.tile_size = tile_size
        self.biomes = biomes
        self.decor = decor
        self.obstacles = obstacles


class MapGenerator:
    def __init__(self, width, height, tower_x, tower_y):
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
        total = self.cols * self.rows
        water = sum(row.count(WATER) for row in biomes)
        return water / total if total else 0.0

    def _derive_shore(self, biomes):
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
        tuft_assets = [
            "decor/grass_tuft_1.png",
            "decor/grass_tuft_2.png",
            "decor/clover.png",
        ]
        lily_assets = ["decor/lily_pad_1.png", "decor/lily_pad_2.png"]
        reed_assets = ["decor/reeds_1.png", "decor/reeds_2.png"]

        flower_density = GAME_CONFIG["flower_density"]
        flower_threshold = GAME_CONFIG["flower_threshold"]
        tuft_density = GAME_CONFIG["tuft_density"]
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
                    elif rng.random() < tuft_density:
                        decor.append(
                            self._decor_item(rng.choice(tuft_assets), cx, cy, rng, ts)
                        )
        return decor

    def _decor_item(self, asset, cx, cy, rng, ts):
        jitter = ts * 0.3
        return {
            "asset": asset,
            "x": cx + rng.uniform(-jitter, jitter),
            "y": cy + rng.uniform(-jitter, jitter),
        }

    def _place_obstacles(self, biomes, rng):
        specs = GAME_CONFIG["land_obstacles"]
        target = GAME_CONFIG["land_obstacle_count"]
        obstacles = []
        attempts = 0
        while len(obstacles) < target and attempts < target * 60:
            attempts += 1
            spec = rng.choice(specs)
            w, h = spec["size"]
            x = rng.uniform(w, self.width - w)
            y = rng.uniform(h, self.height - h)
            if self._is_safe_world(x, y):
                continue
            if self._biome_at(biomes, x, y) != GRASS:
                continue
            obstacle = Obstacle(
                x=x,
                y=y,
                width=w,
                height=h,
                asset=spec["asset"],
                solid=spec.get("solid", True),
            )
            if self._overlaps(obstacle, obstacles):
                continue
            obstacles.append(obstacle)
        return obstacles

    def _overlaps(self, obstacle, others):
        ox, oy, ow, oh = obstacle.rect
        padded = (ox - 18, oy - 18, ow + 36, oh + 36)
        for other in others:
            if _rects_overlap(padded, other.rect):
                return True
        return False

    def _biome_at(self, biomes, x, y):
        col = int(x / self.tile_size)
        row = int(y / self.tile_size)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return biomes[row][col]

    def _tower_tile(self):
        col = int(self.tower_x / self.tile_size)
        row = int(self.tower_y / self.tile_size)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    def _is_border_tile(self, col, row):
        return col == 0 or row == 0 or col == self.cols - 1 or row == self.rows - 1

    def _is_safe_tile(self, col, row):
        cx = col * self.tile_size + self.tile_size / 2
        cy = row * self.tile_size + self.tile_size / 2
        return self._is_safe_world(cx, cy)

    def _is_safe_world(self, x, y):
        return math.hypot(x - self.tower_x, y - self.tower_y) < self.safe_radius


def _rects_overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by
