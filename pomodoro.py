#!/usr/bin/env python3
"""
番茄钟桌面应用 — Pomodoro Timer
功能：25分钟工作 + 5分钟休息循环、任务列表、自定义时长、完成统计、提示音
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import os
import winsound

# ---------- 图片处理 ----------
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ---------- 常量 ----------
CONFIG_FILE = "pomodoro_config.json"
DEFAULT_WORK = 25 * 60
DEFAULT_BREAK = 5 * 60
DEFAULT_LONG_BREAK = 15 * 60
BG_IMAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "微信图片_20260523093444_9_20.jpg")
BG_COLOR = "#f2f7fb"


class PomodoroApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🍅 番茄钟")
        self.root.geometry("520x680")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        # ---------- 加载并设置背景图 ----------
        self.bg_photo = None
        self.bg_label = None
        self.setup_background()

        # ---------- 状态变量 ----------
        self.work_duration = DEFAULT_WORK
        self.break_duration = DEFAULT_BREAK
        self.long_break_duration = DEFAULT_LONG_BREAK
        self.time_left = self.work_duration
        self.is_running = False
        self.is_paused = False
        self.is_work = True
        self.pomodoro_count = 0
        self.timer_thread = None
        self.current_task = None

        self.load_config()
        self.build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_background(self):
        """加载背景图片并作为底层放置"""
        if not HAS_PIL or not os.path.exists(BG_IMAGE):
            return
        try:
            img = Image.open(BG_IMAGE)
            img = img.resize((520, 680), Image.LANCZOS)
            # 降低不透明度，变淡作为背景
            overlay = Image.new("RGBA", img.size, (255, 255, 255, 140))
            img = img.convert("RGBA")
            img = Image.alpha_composite(img, overlay)
            img = img.convert("RGB")
            self.bg_photo = ImageTk.PhotoImage(img)
            self.bg_label = tk.Label(self.root, image=self.bg_photo, bg=BG_COLOR)
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
            self.bg_label.lower()  # 放到最底层
        except Exception as e:
            print(f"背景图加载失败: {e}")

    # ===================== 界面构建 =====================

    def build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Microsoft YaHei", 10), padding=6)
        style.configure("TLabel", font=("Microsoft YaHei", 10), background=BG_COLOR)
        style.configure("TEntry", font=("Microsoft YaHei", 10))
        style.configure("TLabelframe", background=BG_COLOR, font=("Microsoft YaHei", 10, "bold"))
        style.configure("TLabelframe.Label", background=BG_COLOR)

        # -- 顶部标题 --
        self.title_label = ttk.Label(
            self.root, text="🍅 番茄工作法",
            font=("Microsoft YaHei", 18, "bold"), background=BG_COLOR, foreground="#e74c3c"
        )
        self.title_label.pack(pady=(15, 5))

        # -- 状态标签 --
        self.status_label = ttk.Label(
            self.root, text="准备开始工作",
            font=("Microsoft YaHei", 11), background=BG_COLOR, foreground="#666"
        )
        self.status_label.pack()

        # -- 计时器圆形显示 --
        self.timer_canvas = tk.Canvas(
            self.root, width=220, height=220,
            bg=BG_COLOR, highlightthickness=0
        )
        self.timer_canvas.pack(pady=(10, 5))
        self.draw_timer_circle(self.work_duration, self.work_duration)

        # -- 控制按钮 --
        control_frame = tk.Frame(self.root, bg=BG_COLOR)
        control_frame.pack(pady=8)

        self.start_btn = ttk.Button(control_frame, text="▶ 开始", command=self.toggle_timer)
        self.start_btn.pack(side=tk.LEFT, padx=4)

        self.reset_btn = ttk.Button(control_frame, text="↺ 重置", command=self.reset_timer)
        self.reset_btn.pack(side=tk.LEFT, padx=4)

        self.skip_btn = ttk.Button(control_frame, text="⏭ 跳过", command=self.skip_timer)
        self.skip_btn.pack(side=tk.LEFT, padx=4)

        # -- 设置区域 --
        settings_frame = ttk.LabelFrame(self.root, text="⏱ 时长设置（分钟）", padding=10)
        settings_frame.pack(fill=tk.X, padx=20, pady=6)

        ttk.Label(settings_frame, text="工作：").grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.work_var = tk.IntVar(value=self.work_duration // 60)
        self.work_spin = ttk.Spinbox(
            settings_frame, from_=1, to=120, textvariable=self.work_var,
            width=5, command=self.on_setting_change
        )
        self.work_spin.grid(row=0, column=1, padx=(0, 16))

        ttk.Label(settings_frame, text="短休息：").grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.break_var = tk.IntVar(value=self.break_duration // 60)
        self.break_spin = ttk.Spinbox(
            settings_frame, from_=1, to=60, textvariable=self.break_var,
            width=5, command=self.on_setting_change
        )
        self.break_spin.grid(row=0, column=3, padx=(0, 16))

        ttk.Label(settings_frame, text="长休息：").grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.long_break_var = tk.IntVar(value=self.long_break_duration // 60)
        self.long_break_spin = ttk.Spinbox(
            settings_frame, from_=1, to=120, textvariable=self.long_break_var,
            width=5, command=self.on_setting_change
        )
        self.long_break_spin.grid(row=0, column=5)

        # -- 统计信息 --
        stats_frame = ttk.LabelFrame(self.root, text="📊 统计", padding=10)
        stats_frame.pack(fill=tk.X, padx=20, pady=4)

        self.stats_label = ttk.Label(
            stats_frame,
            text=f"今日完成：0 个番茄 | 总计：{self.pomodoro_count} 个番茄",
            font=("Microsoft YaHei", 10)
        )
        self.stats_label.pack()

        # -- 任务列表 --
        task_frame = ttk.LabelFrame(self.root, text="📋 任务列表", padding=10)
        task_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=4)

        input_frame = tk.Frame(task_frame, bg=BG_COLOR)
        input_frame.pack(fill=tk.X, pady=(0, 6))

        self.task_entry = ttk.Entry(input_frame, font=("Microsoft YaHei", 10))
        self.task_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        add_btn = ttk.Button(input_frame, text="＋ 添加", command=self.add_task)
        add_btn.pack(side=tk.RIGHT)

        self.task_tree = ttk.Treeview(
            task_frame, columns=("status", "task"),
            show="headings", height=8, selectmode="browse"
        )
        self.task_tree.heading("status", text="")
        self.task_tree.heading("task", text="任务")
        self.task_tree.column("status", width=30, anchor="center")
        self.task_tree.column("task", width=400)
        self.task_tree.pack(fill=tk.BOTH, expand=True)

        task_btn_frame = tk.Frame(task_frame, bg=BG_COLOR)
        task_btn_frame.pack(fill=tk.X, pady=(6, 0))

        self.complete_btn = ttk.Button(task_btn_frame, text="✓ 完成", command=self.complete_task)
        self.complete_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.delete_btn = ttk.Button(task_btn_frame, text="✗ 删除", command=self.delete_task)
        self.delete_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.select_task_btn = ttk.Button(task_btn_frame, text="📌 选为当前任务", command=self.select_task)
        self.select_task_btn.pack(side=tk.LEFT)

    # ===================== 计时器绘制 =====================

    def draw_timer_circle(self, total, remaining):
        self.timer_canvas.delete("all")
        x, y, r = 110, 110, 90

        self.timer_canvas.create_oval(
            x - r, y - r, x + r, y + r,
            outline="#e0e0e0", width=8
        )

        if total > 0:
            extent = (remaining / total) * 360
            self.timer_canvas.create_arc(
                x - r, y - r, x + r, y + r,
                start=90, extent=extent * -1,
                outline="#e74c3c" if self.is_work else "#2ecc71",
                width=8, style="arc"
            )

        mins, secs = divmod(remaining, 60)
        time_text = f"{mins:02d}:{secs:02d}"
        self.timer_canvas.create_text(
            x, y - 12, text=time_text,
            font=("Consolas", 36, "bold"), fill="#333"
        )

        mode_text = "🔴 雷霆导管" if self.is_work else "🟢 休息"
        self.timer_canvas.create_text(
            x, y + 30, text=mode_text,
            font=("Microsoft YaHei", 16, "bold"), fill="#ffc107"
        )

    # ===================== 计时器控制 =====================

    def toggle_timer(self):
        if not self.is_running:
            self.start_timer()
        else:
            self.pause_timer()

    def start_timer(self):
        if self.is_paused:
            self.is_paused = False
            self.is_running = True
        else:
            self.is_running = True
            self.is_paused = False

        self.start_btn.config(text="⏸ 暂停")
        self.status_label.config(
            text="工作中..." if self.is_work else "休息中..."
        )
        self.disable_settings(True)

        self.timer_thread = threading.Thread(target=self.countdown, daemon=True)
        self.timer_thread.start()

    def pause_timer(self):
        self.is_running = False
        self.is_paused = True
        self.start_btn.config(text="▶ 继续")
        self.status_label.config(text="已暂停")

    def reset_timer(self):
        self.is_running = False
        self.is_paused = False
        self.time_left = self.work_duration
        self.is_work = True
        self.start_btn.config(text="▶ 开始")
        self.status_label.config(text="准备开始工作")
        self.disable_settings(False)
        self.draw_timer_circle(self.work_duration, self.work_duration)

    def skip_timer(self):
        self.is_running = False
        self.is_paused = False
        if self.is_work:
            self.switch_mode()
        else:
            self.time_left = self.work_duration
            self.is_work = True
            self.reset_timer()
            self.draw_timer_circle(self.work_duration, self.work_duration)

    def countdown(self):
        total = self.time_left
        while self.is_running and self.time_left > 0:
            time.sleep(1)
            if not self.is_running:
                break
            self.time_left -= 1
            self.root.after(0, self.update_display, total)

        if self.time_left <= 0 and self.is_running:
            self.root.after(0, self.timer_finished)

    def update_display(self, total):
        self.draw_timer_circle(
            self.work_duration if self.is_work else self.break_duration,
            self.time_left
        )

    def timer_finished(self):
        self.is_running = False
        self.is_paused = False
        self.start_btn.config(text="▶ 开始")
        self.disable_settings(False)

        if self.is_work:
            self.pomodoro_count += 1
            self.save_config()
            self.update_stats_display()
            self.status_label.config(text=f"✅ 完成！已累计 {self.pomodoro_count} 个番茄")
            self.play_sound()
            self.show_notification("工作完成！", f"已完成 {self.pomodoro_count} 个番茄，该休息了。")
        else:
            self.status_label.config(text="休息结束，准备下一个番茄！")
            self.play_sound()
            self.show_notification("休息结束！", "准备开始下一个番茄。")

        self.switch_mode()

    def switch_mode(self):
        self.is_work = not self.is_work

        if self.is_work:
            self.time_left = self.work_duration
            self.draw_timer_circle(self.work_duration, self.work_duration)
            self.status_label.config(text="准备开始工作")
        else:
            if self.pomodoro_count > 0 and self.pomodoro_count % 4 == 0:
                self.break_duration = self.long_break_duration
                self.status_label.config(text="该来一次长休息了～")
            else:
                self.break_duration = self.break_var.get() * 60
            self.time_left = self.break_duration
            self.draw_timer_circle(self.break_duration, self.break_duration)

    def disable_settings(self, disabled):
        state = "disabled" if disabled else "normal"
        self.work_spin.config(state=state)
        self.break_spin.config(state=state)
        self.long_break_spin.config(state=state)

    def on_setting_change(self):
        self.work_duration = self.work_var.get() * 60
        self.break_duration = self.break_var.get() * 60
        self.long_break_duration = self.long_break_var.get() * 60
        self.save_config()
        if not self.is_running and not self.is_paused:
            self.time_left = self.work_duration
            self.draw_timer_circle(self.work_duration, self.work_duration)

    # ===================== 任务管理 =====================

    def add_task(self):
        task_text = self.task_entry.get().strip()
        if not task_text:
            return
        self.task_tree.insert("", tk.END, values=("☐", task_text))
        self.task_entry.delete(0, tk.END)

    def complete_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        values = self.task_tree.item(selected[0], "values")
        if values[0] == "☐":
            self.task_tree.item(selected[0], values=("☑", values[1]))
        else:
            self.task_tree.item(selected[0], values=("☐", values[1]))

    def delete_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        if self.current_task == selected[0]:
            self.current_task = None
            self.status_label.config(text="准备开始工作")
        self.task_tree.delete(selected[0])

    def select_task(self):
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先选择一个任务")
            return
        self.current_task = selected[0]
        task_name = self.task_tree.item(selected[0], "values")[1]
        self.status_label.config(text=f"当前任务：{task_name}")

    # ===================== 统计 =====================

    def update_stats_display(self):
        self.stats_label.config(
            text=f"已完成：{self.pomodoro_count} 个番茄"
        )

    # ===================== 通知和声音 =====================

    def play_sound(self):
        for _ in range(3):
            try:
                winsound.Beep(800, 200)
                time.sleep(0.1)
            except Exception:
                pass

    def show_notification(self, title, message):
        try:
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(200, lambda: self.root.attributes("-topmost", False))
            messagebox.showinfo(title, message)
        except Exception:
            pass

    # ===================== 配置持久化 =====================

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.work_duration = data.get("work_duration", DEFAULT_WORK)
                    self.break_duration = data.get("break_duration", DEFAULT_BREAK)
                    self.long_break_duration = data.get("long_break_duration", DEFAULT_LONG_BREAK)
                    self.pomodoro_count = data.get("pomodoro_count", 0)
                return
            except Exception:
                pass
        self.work_duration = DEFAULT_WORK
        self.break_duration = DEFAULT_BREAK
        self.long_break_duration = DEFAULT_LONG_BREAK
        self.pomodoro_count = 0

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "work_duration": self.work_duration,
                    "break_duration": self.break_duration,
                    "long_break_duration": self.long_break_duration,
                    "pomodoro_count": self.pomodoro_count,
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def on_close(self):
        self.is_running = False
        self.save_config()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroApp(root)

    root.update_idletasks()
    w = root.winfo_width()
    h = root.winfo_height()
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f"{w}x{h}+{x}+{y}")

    root.mainloop()
