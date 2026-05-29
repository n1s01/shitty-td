class Grid:
    def __init__(self, width, height, cols, rows):
        self.cols = cols
        self.rows = rows
        self.cell_w = width / cols
        self.cell_h = height / rows
        self.cells = [[0] * cols for _ in range(rows)]

    def world_to_grid(self, x, y):
        col = int(x / self.cell_w)
        row = int(y / self.cell_h)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    def grid_to_world(self, col, row):
        x = col * self.cell_w + self.cell_w / 2
        y = row * self.cell_h + self.cell_h / 2
        return x, y

    def is_walkable(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.cells[row][col] == 0
        return False

    def set_obstacle(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.cells[row][col] = 1

    def remove_obstacle(self, col, row):
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.cells[row][col] = 0

    def get_neighbors(self, col, row):
        neighbors = []
        for dc, dr in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            nc, nr = col + dc, row + dr
            if self.is_walkable(nc, nr):
                neighbors.append((nc, nr))
        return neighbors
