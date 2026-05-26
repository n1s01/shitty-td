import tkinter as tk
from config import COLORS, GAME_CONFIG
from core.game_engine import GameEngine


class GameScreen(tk.Frame):
    def __init__(self, master, width, height, on_back):
        super().__init__(master)
        self.master = master
        self.width = width
        self.height = height
        self.on_back = on_back

        self.canvas = tk.Canvas(
            self,
            width=self.width,
            height=self.height,
            bg=COLORS["canvas_bg"],
            highlightthickness=0,
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.back_btn = tk.Button(
            self,
            text="В меню",
            command=self.exit_to_menu,
            bg=COLORS["back_button_bg"],
            fg=COLORS["back_button_fg"],
        )
        self.canvas.create_window(50, 25, window=self.back_btn)

        self.engine = GameEngine(self.width, self.height)
        self.canvas.bind("<Button-1>", self.on_click)

        self.is_running = True
        self.game_loop()

    def game_loop(self):
        if not self.is_running:
            return

        self.engine.update()
        self.render()

        if self.engine.is_game_over:
            self.game_over()
            return

        self.master.after(GAME_CONFIG["frame_time_ms"], self.game_loop)

    def on_click(self, event):
        self.engine.shoot_at(event.x, event.y)

    def render(self):
        self.canvas.delete("game_object")
        self._render_tower()
        self._render_enemies()
        self._render_projectiles()

    def _render_tower(self):
        tower = self.engine.tower
        half_size = tower.size / 2
        self.canvas.create_rectangle(
            tower.x - half_size,
            tower.y - half_size,
            tower.x + half_size,
            tower.y + half_size,
            fill=COLORS["tower_fill"],
            outline=COLORS["tower_outline"],
            width=3,
            tags="game_object",
        )
        self.canvas.create_text(
            tower.x,
            tower.y - half_size - 15,
            text=f"HP: {tower.hp}",
            fill=COLORS["tower_text"],
            font=("Arial", 12, "bold"),
            tags="game_object",
        )

    def _render_enemies(self):
        for enemy in self.engine.enemies:
            r = enemy.size / 2
            self.canvas.create_oval(
                enemy.x - r,
                enemy.y - r,
                enemy.x + r,
                enemy.y + r,
                fill=COLORS["enemy_fill"],
                outline=COLORS["enemy_outline"],
                width=2,
                tags="game_object",
            )

            if enemy.hp < enemy.max_hp:
                self._render_enemy_hp(enemy, r)

    def _render_enemy_hp(self, enemy, r):
        bar_w = enemy.size
        pct = enemy.hp / enemy.max_hp
        self.canvas.create_rectangle(
            enemy.x - bar_w / 2,
            enemy.y - r - 8,
            enemy.x + bar_w / 2,
            enemy.y - r - 5,
            fill=COLORS["enemy_hp_bg"],
            outline="",
            tags="game_object",
        )
        self.canvas.create_rectangle(
            enemy.x - bar_w / 2,
            enemy.y - r - 8,
            enemy.x - bar_w / 2 + (bar_w * pct),
            enemy.y - r - 5,
            fill=COLORS["enemy_hp_fg"],
            outline="",
            tags="game_object",
        )

    def _render_projectiles(self):
        proj_size = GAME_CONFIG["projectile_size"]
        for proj in self.engine.projectiles:
            self.canvas.create_oval(
                proj.x - proj_size,
                proj.y - proj_size,
                proj.x + proj_size,
                proj.y + proj_size,
                fill=COLORS["projectile_fill"],
                outline="",
                tags="game_object",
            )

    def game_over(self):
        self.is_running = False
        self.canvas.create_text(
            self.engine.tower.x,
            self.engine.tower.y,
            text="ИГРА ОКОНЧЕНА",
            fill=COLORS["game_over_text"],
            font=("Arial", 28, "bold"),
            tags="game_object",
        )

    def exit_to_menu(self):
        self.is_running = False
        self.on_back()
