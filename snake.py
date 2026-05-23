"""
贪吃蛇 — tkinter 桌面版（无需额外依赖）
方向键/WASD 控制 | P 暂停 | R 重新开始 | Q 退出
吃食物变长，速度逐渐加快，撞墙或撞自己游戏结束
"""

import tkinter as tk
import random
from collections import deque

# ==================== 配置 ====================
CELL = 26                      # 每格像素
COLS, ROWS = 25, 20            # 网格列数、行数
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
BAR_HEIGHT = 42                # 顶部状态栏高度
FPS_BASE = 120                 # 基础游戏速度（毫秒/帧）
FPS_MIN = 50                   # 最快速度
SPEED_STEP = 8                 # 每次加速缩小的毫秒数
FOODS_PER_SPEEDUP = 3          # 每吃 3 个食物加速一次

# 颜色
BG = "#1c1c1e"
GRID_LINE = "#2c2c30"
SNAKE_BODY = "#62c876"
SNAKE_HEAD = "#82e68c"
FOOD_COLOR = "#ff5f5f"
TEXT_COLOR = "#dcdcdc"
SCORE_COLOR = "#ffc83c"


class Game:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🐍 贪吃蛇")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        # 用 Frame 包住 Canvas，保持窗口大小稳定
        self.canvas = tk.Canvas(
            self.root, width=WIDTH, height=HEIGHT + BAR_HEIGHT,
            bg=BG, highlightthickness=0
        )
        self.canvas.pack()

        # 绑定键盘
        self.root.bind("<KeyPress>", self.on_key)

        # 状态
        self.reset()
        self.draw_grid()
        self.tick()

        # 窗口居中
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

        self.root.mainloop()

    def reset(self):
        """初始化/重置游戏"""
        cx, cy = COLS // 2, ROWS // 2
        self.snake = deque([(cx, cy), (cx - 1, cy), (cx - 2, cy)])
        self.direction = (1, 0)        # 当前方向
        self.next_dir = (1, 0)         # 缓冲方向（防止一帧内反向）
        self.grow_next = False
        self.score = 0
        self.speed = FPS_BASE          # 毫秒
        self.state = "playing"         # playing | paused | over
        self.death_reason = ""
        self.food = self.spawn_food()

    def spawn_food(self):
        """在空位置生成食物"""
        while True:
            pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
            if pos not in self.snake:
                return pos

    # ==================== 键盘事件 ====================

    def on_key(self, event):
        key = event.keysym

        if key == "q" or key == "Q":
            self.root.destroy()
            return

        if key == "r" or key == "R":
            if self.state == "over":
                self.reset()
                self.draw_grid()
            return

        if key == "p" or key == "P":
            if self.state == "playing":
                self.state = "paused"
                self.draw()
            elif self.state == "paused":
                self.state = "playing"
            return

        if self.state != "playing":
            return

        # 方向映射
        dir_map = {
            "Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0),
            "w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
            "W": (0, -1), "S": (0, 1), "A": (-1, 0), "D": (1, 0),
        }
        if key in dir_map:
            new_dir = dir_map[key]
            dx, dy = self.direction
            # 禁止 180° 掉头
            if (new_dir[0] + dx, new_dir[1] + dy) != (0, 0):
                self.next_dir = new_dir

    # ==================== 游戏逻辑 ====================

    def update(self):
        """每帧更新"""
        self.direction = self.next_dir
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # 撞墙
        if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
            self.state = "over"
            self.death_reason = "撞墙"
            self.draw()
            return

        # 撞自己
        if new_head in self.snake:
            self.state = "over"
            self.death_reason = "咬到自己"
            self.draw()
            return

        # 移动
        self.snake.appendleft(new_head)
        if self.grow_next:
            self.grow_next = False
        else:
            self.snake.pop()

        # 吃食物
        if self.snake[0] == self.food:
            self.grow_next = True
            self.food = self.spawn_food()
            self.score += 1
            # 加速
            if self.score % FOODS_PER_SPEEDUP == 0:
                self.speed = max(self.speed - SPEED_STEP, FPS_MIN)

    # ==================== 绘制 ====================

    def draw_grid(self):
        """绘制背景网格（只在重置时调用）"""
        self.canvas.delete("grid")
        for x in range(0, WIDTH, CELL):
            self.canvas.create_line(
                x, BAR_HEIGHT, x, HEIGHT + BAR_HEIGHT,
                fill=GRID_LINE, tags="grid"
            )
        for y in range(BAR_HEIGHT, HEIGHT + BAR_HEIGHT, CELL):
            self.canvas.create_line(
                0, y, WIDTH, y,
                fill=GRID_LINE, tags="grid"
            )

    def draw(self):
        """每帧重绘蛇、食物、状态栏"""
        self.canvas.delete("dynamic")

        # ---------- 状态栏 ----------
        self.canvas.create_rectangle(
            0, 0, WIDTH, BAR_HEIGHT, fill="#141416", outline="", tags="dynamic"
        )
        # 分隔线
        self.canvas.create_line(
            0, BAR_HEIGHT, WIDTH, BAR_HEIGHT,
            fill="#3a3a3e", width=2, tags="dynamic"
        )

        score_str = f"🏆 {self.score}"
        self.canvas.create_text(
            14, BAR_HEIGHT // 2,
            text=score_str, anchor="w", fill=SCORE_COLOR,
            font=("Microsoft YaHei", 13, "bold"), tags="dynamic"
        )

        speed_str = f"速度: {(FPS_BASE - self.speed) // SPEED_STEP + 1}"
        self.canvas.create_text(
            130, BAR_HEIGHT // 2,
            text=speed_str, anchor="w", fill=TEXT_COLOR,
            font=("Microsoft YaHei", 10), tags="dynamic"
        )

        hint = "方向键/WASD 移动 | P 暂停 | R 重来 | Q 退出"
        self.canvas.create_text(
            WIDTH - 14, BAR_HEIGHT // 2,
            text=hint, anchor="e", fill="#888",
            font=("Microsoft YaHei", 9), tags="dynamic"
        )

        # ---------- 蛇 ----------
        for i, (gx, gy) in enumerate(self.snake):
            x1 = gx * CELL + 1
            y1 = gy * CELL + BAR_HEIGHT + 1
            x2 = x1 + CELL - 2
            y2 = y1 + CELL - 2
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline="", tags="dynamic"
            )

        # ---------- 食物 ----------
        fx, fy = self.food
        cx = fx * CELL + CELL // 2
        cy = fy * CELL + BAR_HEIGHT + CELL // 2
        # 脉冲效果
        import time as _time
        pulse = abs((_time.time() * 4) % 2 - 1)
        r = int(CELL / 2 - 3 + pulse * 2)
        self.canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            fill=FOOD_COLOR, outline="#ff8888", width=1, tags="dynamic"
        )

        # ---------- 暂停遮罩 ----------
        if self.state == "paused":
            self.draw_overlay("⏸ 已暂停", "按 P 继续")

        # ---------- 结束遮罩 ----------
        if self.state == "over":
            self.draw_overlay(
                f"游戏结束 ({self.death_reason})",
                f"得分: {self.score} | 按 R 重新开始"
            )

    def draw_overlay(self, title, subtitle):
        """半透明遮罩"""
        self.canvas.create_rectangle(
            0, 0, WIDTH, HEIGHT + BAR_HEIGHT,
            fill="#000000", stipple="gray50", tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + BAR_HEIGHT // 2 - 16,
            text=title, fill="#fff",
            font=("Microsoft YaHei", 20, "bold"), tags="dynamic"
        )
        self.canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + BAR_HEIGHT // 2 + 20,
            text=subtitle, fill="#ccc",
            font=("Microsoft YaHei", 13), tags="dynamic"
        )

    # ==================== 主循环 ====================

    def tick(self):
        """游戏主循环"""
        if self.state == "playing":
            self.update()
            self.draw()

        if self.state == "over" or self.state == "paused":
            self.draw()

        self.root.after(self.speed, self.tick)


if __name__ == "__main__":
    Game()
