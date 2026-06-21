"""Сетка игрового поля: перевод координат и проходимость клеток."""


class Grid:
    """Прямоугольная сетка из клеток `cols` x `rows`.

    Хранит, какие клетки заняты препятствиями, и переводит координаты
    между миром (пиксели) и сеткой (номера колонки и строки).
    """

    def __init__(self, width, height, cols, rows):
        """Создаёт сетку и вычисляет размер одной клетки.

        Args:
            width: ширина поля в пикселях.
            height: высота поля в пикселях.
            cols: количество колонок.
            rows: количество строк.
        """
        self.cols = cols
        self.rows = rows
        self.cell_w = width / cols
        self.cell_h = height / rows
        self.cells = [[0] * cols for _ in range(rows)]

    def world_to_grid(self, x, y):
        """Переводит координаты мира в номера клетки.

        Args:
            x: координата по горизонтали в пикселях.
            y: координата по вертикали в пикселях.

        Returns:
            Кортеж (col, row) - номер колонки и строки, обрезанный
            до границ сетки.
        """
        col = int(x / self.cell_w)
        row = int(y / self.cell_h)
        col = max(0, min(col, self.cols - 1))
        row = max(0, min(row, self.rows - 1))
        return col, row

    def grid_to_world(self, col, row):
        """Возвращает координаты центра клетки в мире.

        Args:
            col: номер колонки.
            row: номер строки.

        Returns:
            Кортеж (x, y) - координаты центра клетки в пикселях.
        """
        x = col * self.cell_w + self.cell_w / 2
        y = row * self.cell_h + self.cell_h / 2
        return x, y

    def is_walkable(self, col, row):
        """Проверяет, можно ли пройти через клетку.

        Args:
            col: номер колонки.
            row: номер строки.

        Returns:
            True, если клетка в пределах сетки и не занята препятствием,
            иначе False.
        """
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return self.cells[row][col] == 0
        return False

    def set_obstacle(self, col, row):
        """Помечает клетку как занятую препятствием.

        Args:
            col: номер колонки.
            row: номер строки.
        """
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.cells[row][col] = 1

    def remove_obstacle(self, col, row):
        """Убирает препятствие с клетки, делая её проходимой.

        Args:
            col: номер колонки.
            row: номер строки.
        """
        if 0 <= col < self.cols and 0 <= row < self.rows:
            self.cells[row][col] = 0

    def get_neighbors(self, col, row):
        """Возвращает проходимых соседей клетки по 8 направлениям.

        Args:
            col: номер колонки.
            row: номер строки.

        Returns:
            Список кортежей (col, row) соседних проходимых клеток,
            включая диагонали.
        """
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
