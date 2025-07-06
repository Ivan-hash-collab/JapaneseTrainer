# ─── menu.py ───────────────────────────────────────────────────────────────
import random, json, sys, os, pathlib
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import tkinter as tk   
from utils import resource_path, ensure_data_dir
import form_guide                        # окно-шпаргалка

PROGRESS_PATH = "data/progress.json"
# --------------------------------------------------------------------------


# ─────────────────── вспомогательные цвета / стили ─────────────────────────
DARK_TURQ  = "#007A7A"     # тёмно-бирюзовый (кнопки)
DARK_BLUE  = "#002B5B"     # насыщенный синий   (факт + совет)
BTN_STYLE_NAME = "Turq.TButton"


def init_custom_styles(style: tb.Style) -> None:
    """
    Регистрирует стиль `Turq.TButton` 1 раз на всё приложение.
    Вызывать сразу после создания окна-root.
    """
    if BTN_STYLE_NAME in style.element_names():
        return                                                   # уже есть

    style.configure(
        BTN_STYLE_NAME,
        foreground=DARK_TURQ,
        font=("Segoe UI", 10, "bold"),
        padding=(10, 4),
        borderwidth=1,
        relief="raised",
    )
    style.map(
        BTN_STYLE_NAME,
        foreground=[("pressed", DARK_TURQ), ("active", DARK_TURQ)],
        background=[("pressed", style.colors.light),
                    ("active",  style.colors.light)],
    )
# --------------------------------------------------------------------------


class MainMenu:
    """Стартовое меню тренажёра грамматических конструкций и форм."""

    BUILTIN_FORMS = [
        "Te-form", "Negative-form", "Masu-form", "Ta-form",
        "Potential-form", "Passive-form", "Causative-form", "Imperative-form",
        "Volitional-form", "Ba-form", "Tara-form",
        "Masu-stem", "Progressive-form", "Command-form"
    ]

    # ─────────────────── инициализация ───────────────────
    def __init__(self):
        # ── копируем data/ при первом запуске ──
        ensure_data_dir([
            "facts_200.json", "lessons.json",
            "grammar_n5.json", "grammar_n4.json", "grammar_n3.json",
            "grammar_constructions.json", "conjugation_table_with_translations.json"
        ])

        # ── корневое окно TTK-Bootstrap ──
        self.root = tb.Window(themename="minty")
        self.root.title("Тренажёр грамматики / форм")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        init_custom_styles(self.root.style)    # регистрируем стиль кнопок

        # ── переменные состояния ──
        self.user_name      = tb.StringVar()
        self.user_level     = tb.StringVar(value="N5")
        self.mode           = tb.StringVar(value="grammar")
        self.grammar_source = tb.StringVar(value="builtin")

        self.imported_grammar  : list[str]        = []
        self.remaining_grammar : list             = []
        self.remaining_forms   = MainMenu.BUILTIN_FORMS.copy()
        self.selected_count    = tb.IntVar(value=5)

        self.load_progress()      # восстановим (если есть)

        # ── статические метки ──
        lbl_font = ("Segoe UI", 10, "bold")
        self.greeting_label = tb.Label(self.root,
                                       font=("Segoe UI", 30, "italic"),
                                       bootstyle="info", wraplength=500)

        self.fact_label   = tb.Label(self.root, font=lbl_font,
                                     foreground=DARK_BLUE,
                                     wraplength=500, justify="left")

        self.grammar_label = tb.Label(self.root, font=lbl_font,
                                     foreground=DARK_BLUE,
                                     wraplength=500)

        self.advice_label = tb.Label(self.root, font=lbl_font,
                                     foreground=DARK_BLUE,
                                     wraplength=500)

        self.counts_label = tb.Label(self.root, bootstyle="light")

        # наполним случайной информацией
        self.fact_label  .config(text=self.get_random_fact())
        self.advice_label.config(text=self.get_random_advice())

        self.build_ui()
        # когда пользователь переключает N5/N4/N3, счётчик также меняется
        self.user_level.trace_add("write", lambda *_: self.use_builtin_grammar())

        # нарисуем первую актуальную цифру
        self.update_counts_label()

    # ─────────────────── «каркас» UI ───────────────────
    def build_ui(self):
        fr = tb.Frame(self.root, padding=10)
        fr.pack(fill=BOTH, expand=YES)

        tb.Label(fr, text="Тренажёр японской грамматики / форм",
                 font=("Segoe UI", 13, "bold"),
                 bootstyle="primary", wraplength=500).pack()

        self.greeting_label.pack()

        tb.Label(
            fr,
            text=("Выберите режим, уровень и количество элементов, "
                  "затем нажмите ▶ для повторения."),
            bootstyle="light", wraplength=500, justify="left"
        ).pack(pady=(0, 10))

        # --- поля ввода / настройки ---------------------------------------
        tb.Label(fr, text="Имя:").pack(anchor="w")
        tb.Entry(fr, textvariable=self.user_name).pack(fill=X)

        tb.Label(fr, text="Повторяем:").pack(anchor="w", pady=(10, 0))
        tb.Combobox(fr, textvariable=self.mode,
                    values=["grammar", "forms"], state="readonly").pack(fill=X)

        tb.Label(fr, text="Уровень (для грамматики):").pack(anchor="w", pady=(10, 0))
        tb.Combobox(fr, textvariable=self.user_level,
                    values=["N5", "N4", "N3"], state="readonly").pack(fill=X)

        tb.Button(fr, text="Импортировать список грамматики",
                  style=BTN_STYLE_NAME, command=self.import_grammar_list).pack(pady=5)

        tb.Label(fr, text="Элементов сегодня:").pack(anchor="w", pady=(10, 0))
        tb.Entry(fr, textvariable=self.selected_count, width=5).pack()

        # --- 4 главные кнопки (единый стиль) ------------------------------
        tb.Button(
            fr, text="🎲 Случайная грамматика",
            style=BTN_STYLE_NAME,
            command=lambda: self.grammar_label.config(text=self.get_random_grammar())
        ).pack(pady=5)

        self.fact_label.pack(pady=3)
        self.grammar_label.pack(pady=3)
        self.advice_label.pack(pady=3)

        tb.Button(fr, text="🔄 Сбросить прогресс",
                  style=BTN_STYLE_NAME, command=self.reset_progress).pack(pady=(8, 2))

        tb.Button(fr, text="▶ Начать повторение",
                  style=BTN_STYLE_NAME, command=self.start_session).pack(pady=2)

        self.counts_label = tb.Label(
            fr,
            bootstyle="info",
            font=("Segoe UI", 10, "bold")
        )
        

        tb.Button(fr, text="📖 Шпаргалка по формам",
                  style=BTN_STYLE_NAME, command=self.open_form_guide).pack(pady=(6, 0))
                  
        self.counts_label.pack(pady=(10, 0)) 

    
    def use_builtin_grammar(self):
        """Переключаемся на встроенный список (N5/N4/N3)."""
        self.grammar_source.set("builtin")
        self.remaining_grammar.clear()       # заставим перечитать файл
        self.update_counts_label()
        
    # ─────────────────── «случайные» тексты ───────────────────────────────
    def get_random_fact(self):
        try:
            with open("data/facts_200.json", encoding="utf-8") as f:
                return "🎌 " + random.choice(json.load(f))
        except Exception as e:
            return f"🎌 (факт не загружен: {e})"

    def get_random_advice(self):
        tips = [
            "Повторяйте вслух для лучшей памяти.",
            "Используйте интервальное повторение.",
            "Смотрите видео на японском с субтитрами.",
            "Ведите краткий дневник на японском."
        ]
        return "💡 " + random.choice(tips)

    def get_random_grammar(self):
        try:
            lvl = self.user_level.get().lower()
            with open(f"data/grammar_{lvl}.json", encoding="utf-8") as f:
                g = random.choice(json.load(f))
            return f"📚 {g['title']} — {g['comment']}"
        except Exception as e:
            return f"📚 (грамматика не загружена: {e})"

    # ─────────────────── импорт / сброс / подсчёт ─────────────────────────
    def import_grammar_list(self):
        path = filedialog.askopenfilename(
            title="Выберите .txt со списком конструкций",
            filetypes=[("Text files", "*.txt")])

        # Подсказка о формате
        messagebox.showinfo(
            "Формат файла",
            "В файле каждая конструкция должна быть\n"
            "расположена на отдельной строке.\n"
            "Пустые строки игнорируются."
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                self.imported_grammar = [ln.strip() for ln in f if ln.strip()]
                if not self.imported_grammar:
                    messagebox.showwarning("Импорт", "Файл пуст или все строки пустые!")
                    return
            self.remaining_grammar = self.imported_grammar.copy()
            self.grammar_source.set("imported")
            messagebox.showinfo("Импорт", f"Импортировано {len(self.imported_grammar)} конструкций.")
            self.update_counts_label()
            self.save_progress()
        except Exception as e:
            messagebox.showerror("Ошибка импорта", e)

    def reset_progress(self):
        """Полный сброс: снова встроенные списки + обнулить счётчики."""
        self.grammar_source.set("builtin")          # ← ключевая строка
        self.remaining_forms   = MainMenu.BUILTIN_FORMS.copy()
        self.remaining_grammar = []                 # будет перезаполнен
        self.ensure_builtin_loaded()
        self.update_counts_label()
        messagebox.showinfo("Сброс", "Прогресс обнулён.")
        self.save_progress()

    # помощник: загружаем встроенный список N5/N4/N3 при первом обращении
    def ensure_builtin_loaded(self):
        if self.remaining_grammar:
            return
        lvl = self.user_level.get().lower()
        try:
            with open(f"data/grammar_{lvl}.json", encoding="utf-8") as f:
                self.remaining_grammar = [
                    (g["title"], g.get("comment", "")) for g in json.load(f)
                ]
        except Exception as e:
            messagebox.showerror("Ошибка", e)
            
        # ─────────────────── счёт оставшихся конструкций ───────────────────
    ### BEGIN get_remaining_grammar_count ###
    def get_remaining_grammar_count(self) -> int:
        """
        Возвращает количество непройденных грамматических конструкций
        для текущего источника (builtin N5/N4/N3 или imported).
        """
        if self.grammar_source.get() == "builtin":
            # загружаем список, если ещё не загружен
            self.ensure_builtin_loaded()
        return len(self.remaining_grammar)
    ### END get_remaining_grammar_count ###

    def update_counts_label(self):
        g_left = self.get_remaining_grammar_count()
        f_left = len(self.remaining_forms)

        # Читаем, откуда берутся конструкции
        if self.grammar_source.get() == "imported":
            src = "импорт"
        else:
            src = self.user_level.get()

        self.counts_label.config(
            text=f"Осталось   грамматика ({src}) — {g_left}   ·   формы — {f_left}"
        )

    # ─────────────────── сессия «сегодняшние элементы» ────────────────────
    def get_today_items(self):
        n = max(1, self.selected_count.get())
        if self.mode.get() == "forms":
            items = random.sample(self.remaining_forms, min(n, len(self.remaining_forms)))
            self.remaining_forms = [x for x in self.remaining_forms if x not in items]
            self.save_progress()
            return items

        if self.grammar_source.get() == "builtin":
            self.ensure_builtin_loaded()
        src = self.remaining_grammar
        items = random.sample(src, min(n, len(src)))
        self.remaining_grammar = [x for x in src if x not in items]
        self.save_progress()
        return items

    def start_session(self):
        if (name := self.user_name.get().strip()):
            self.greeting_label.config(text=f"👋 Привет, {name}! Поехали!")
        try:
            items = self.get_today_items()
        except Exception as e:
            messagebox.showerror("Ошибка", e)
            return

        win = tb.Toplevel(self.root)
        win.title("Сегодня нужно повторить")
        tb.Label(win, text="Сегодня нужно повторить:",
                 font=("Segoe UI", 11, "bold"),
                 bootstyle="primary").pack(pady=5)

        tbx = tb.Text(win, width=40, height=15, font=("Segoe UI", 12), wrap="word")
        tbx.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scr = tb.Scrollbar(win, orient="vertical", command=tbx.yview)
        scr.pack(side="right", fill="y")
        tbx.configure(yscrollcommand=scr.set)
        
        context_menu = tk.Menu(tbx, tearoff=0)

        def copy_selection():
            try:
                sel = tbx.get(tk.SEL_FIRST, tk.SEL_LAST)
                win.clipboard_clear()
                win.clipboard_append(sel)
            except tk.TclError:
                pass

        context_menu.add_command(label="Копировать", command=copy_selection)

        def show_ctx_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        tbx.bind("<Button-3>", show_ctx_menu)   # Windows / Linux
        tbx.bind("<Button-2>", show_ctx_menu)   # macOS

        def fmt(x):
            if isinstance(x, (list, tuple)) and len(x) == 2:
                t, c = x
                return f"• {t} — {c}"
            return f"• {x}"
        tbx.insert("end", "\n".join(fmt(x) for x in items))
        tbx.config(state="disabled")
        
        win.clipboard_clear()
        win.clipboard_append(tbx.get("1.0", "end").strip())

        tb.Button(win, text="Закрыть", style=BTN_STYLE_NAME, command=win.destroy).pack(pady=5)
        print("[DEBUG]", items, file=sys.stderr)

        self.update_counts_label()

    # ─────────────────── окно-шпаргалка ───────────────────────────────────
    def open_form_guide(self):
        """Скрываем главное меню → открываем окно-шпаргалку."""
        self.root.withdraw()
        top = tb.Toplevel(self.root)

        # создаём шпаргалку
        form_guide.FormGuide(top, self.root)

        def on_close():
            top.destroy()
            self.root.deiconify()
        top.protocol("WM_DELETE_WINDOW", on_close)

    # ─────────────────── сохранение / загрузка прогресса ──────────────────
    def save_progress(self):
        data = {
            "remaining_grammar": self.remaining_grammar,
            "remaining_forms": self.remaining_forms,
            "grammar_source": self.grammar_source.get(),
            "user_level": self.user_level.get(),
            "imported_grammar": self.imported_grammar,
            "selected_count": self.selected_count.get(),
            "user_name": self.user_name.get(),
        }
        try:
            with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[SAVE ERROR] {e}")

    def load_progress(self):
        if not os.path.exists(PROGRESS_PATH):
            return
        try:
            with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)

            # конвертируем ["title", "comment"] → ("title", "comment")
            def list2tuple(x):
                return tuple(x) if isinstance(x, list) and len(x) == 2 else x

            self.remaining_grammar = [list2tuple(x) for x in data.get("remaining_grammar", [])]
            self.remaining_forms   = data.get("remaining_forms", MainMenu.BUILTIN_FORMS.copy())
            self.grammar_source.set(data.get("grammar_source", "builtin"))
            self.user_level.set(data.get("user_level", "N5"))
            self.imported_grammar  = data.get("imported_grammar", [])
            self.selected_count.set(data.get("selected_count", 5))
            self.user_name.set(data.get("user_name", ""))
        except Exception as e:
            print(f"[LOAD ERROR] {e}")

    # ─────────────────── выход — сохраняем прогресс ───────────────────────
    def on_close(self):
        self.save_progress()
        self.root.destroy()

    # ─────────────────── точка входа ───────────────────────────────────────
    def run(self):
        self.root.mainloop()


# ─── запуск как основной скрипт ───────────────────────────────────────────
if __name__ == "__main__":
    MainMenu().run()
# ───────────────────────────────────────────────────────────────────────────
