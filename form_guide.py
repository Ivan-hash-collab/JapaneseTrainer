import ttkbootstrap as tb
from ttkbootstrap.constants import *
import json


# ─────────────────── вспомогательные ───────────────────
def load_lessons(fname="lessons.json"):
    with open(f"data/{fname}", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────── основное приложение ───────────────────
class FormGuide:
    """
    Шпаргалка по формам глаголов:
      • методички по каждой форме
      • список конструкций этой формы
      • таблица спряжения по глаголам
    Можно вернуться в главное меню.
    """

    # ────────────── инициализация ──────────────
    def __init__(self, root, main_menu_root):
        self.root = root
        self.root.title("Шпаргалка: формы глаголов")
        self.main_menu_root = main_menu_root     # понадобится для «Назад»

        self.lessons = load_lessons()

        # ---------- верхняя панель ----------
        self.form_var = tb.StringVar(value=list(self.lessons.keys())[0])

        tb.Combobox(
            root,
            textvariable=self.form_var,
            values=list(self.lessons.keys()),
            state="readonly",
            width=18
        ).grid(row=0, column=0, padx=8, pady=6)

        tb.Button(root, text="Показать методичку",
                  bootstyle="primary, outline",
                  command=self.show_lesson).grid(row=0, column=1, padx=4, pady=6)

        tb.Button(root, text="Грамматические конструкции",
                  bootstyle="primary, outline",
                  command=self.show_constructions).grid(row=0, column=2, padx=4, pady=6)

        tb.Button(root, text="Таблица спряжений",
                  bootstyle="primary, outline",
                  command=self.show_conjugation_table).grid(row=0, column=3, padx=4, pady=6)

        tb.Button(root, text="← Назад в меню",
                  bootstyle="danger, outline",
                  command=self.go_back).grid(row=0, column=4, padx=10, pady=6)

        # ---------- прокручиваемый Text ----------
        txt_fr = tb.Frame(root)
        txt_fr.grid(row=1, column=0, columnspan=5, sticky="nsew", padx=10, pady=10)

        root.grid_rowconfigure(1, weight=1)
        root.grid_columnconfigure(0, weight=1)
        txt_fr.grid_rowconfigure(0, weight=1)
        txt_fr.grid_columnconfigure(0, weight=1)

        self.text_box = tb.Text(
            txt_fr, wrap="word", font=("Segoe UI", 12)
        )
        self.text_box.grid(row=0, column=0, sticky="nsew")

        vsb = tb.Scrollbar(txt_fr, orient=VERTICAL, command=self.text_box.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        self.text_box.configure(yscrollcommand=vsb.set)

        # контекстное меню (копировать)
        self.context_menu = tb.Menu(self.text_box, tearoff=0)
        self.context_menu.add_command(label="Копировать",
                                      command=self.copy_selection)
        self.text_box.bind("<Button-3>", self.show_ctx_menu)  # Win / X11
        self.text_box.bind("<Button-2>", self.show_ctx_menu)  # macOS

        # форматирование
        self.text_box.tag_configure("title",      font=("Segoe UI", 16, "bold"))
        self.text_box.tag_configure("subheading", font=("Segoe UI", 14, "bold"),
                                    foreground="#2A6F97")
        self.text_box.tag_configure("case",       font=("Segoe UI", 13, "bold"),
                                    foreground="#444444")

        # показать первую методичку
        self.show_lesson()

    # ────────────── служебное ──────────────
    def show_ctx_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def copy_selection(self):
        try:
            sel = self.text_box.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(sel)
        except Exception:
            pass

    # ---------- helper: убрать Treeview ----------
    def _remove_treeview(self):
        for w in self.root.winfo_children():
            if isinstance(w, tb.Treeview):
                w.destroy()

    # ────────────── вывод методички ──────────────
    def show_lesson(self):
        self._remove_treeview()               # <── главное добавление
        key = self.form_var.get()
        lesson = self.lessons.get(key)
        if not lesson:
            return
        tbx = self.text_box
        tbx.delete("1.0", "end")

        tbx.insert("end", lesson["title"] + "\n\n", "title")

        tbx.insert("end", "📌 Описание:\n", "subheading")
        tbx.insert("end", lesson["description"] + "\n\n")

        tbx.insert("end", "🧠 Юзкейсы:\n", "subheading")
        for case, data in lesson["use_cases"].items():
            tbx.insert("end", case + "\n", "case")
            if note := data.get("note"):
                tbx.insert("end", "　" + note + "\n")
            for ex in data["examples"]:
                tbx.insert("end",
                           f"  ・{ex['ja']}\n    {ex['hiragana']}\n    {ex['ru']}\n\n")

        tbx.insert("end", "🔧 Образование:\n", "subheading")
        form = lesson["formation"]
        if ov := form.get("overview"):
            tbx.insert("end", ov + "\n\n")

        for grp in ("group_1", "group_2", "group_3"):
            if grp_data := form.get(grp):
                tbx.insert("end", f"【{grp_data['rule']}】\n", "case")
                for pat, ex in grp_data["patterns"].items():
                    tbx.insert("end", f"  - {pat}: {ex}\n")
                tbx.insert("end", "\n")

    # ────────────── конструкции ──────────────
    def show_constructions(self):
        self._remove_treeview()               # <── тоже добавили
        try:
            with open("data/grammar_constructions.json", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", f"Ошибка: {e}")
            return

        form = self.form_var.get()
        items = [c for c in data if c.get("form") == form]
        if not items:
            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", f"Конструкций для {form} нет.")
            return

        jlpt_order = {"N5": 0, "N4": 1, "N3": 2, "N2": 3, "N1": 4}
        items.sort(key=lambda x: jlpt_order.get(x.get("jlpt", "N5"), 5))

        tbx = self.text_box
        tbx.delete("1.0", "end")
        tbx.insert("end", f"📚 Грамматические конструкции: {form}\n\n", "title")

        for it in items:
            tbx.insert("end",
                       f"🔹 {it['title']} — JLPT {it['jlpt']} — частота: {it['frequency']}%\n",
                       "case")
            tbx.insert("end", it["comment"] + "\n\n")
            for ex in it["examples"]:
                tbx.insert("end", f"・{ex['ja']}\n　{ex['hiragana']}\n　{ex['ru']}\n\n")
            tbx.insert("end", "―" * 40 + "\n\n")

    # ────────────── таблица спряжений ──────────────
    def show_conjugation_table(self):
        # если уже открыт Treeview, сначала убрать его, чтоб не плодились
        self._remove_treeview()

        try:
            with open("data/conjugation_table_with_translations.json",
                      encoding="utf-8") as f:
                table = json.load(f)
        except Exception as e:
            self.text_box.delete("1.0", "end")
            self.text_box.insert("end", f"Ошибка: {e}")
            return

        tv = tb.Treeview(self.root, show="headings", height=28)
        tv.grid(row=1, column=0, columnspan=5, sticky="nsew",
                padx=10, pady=10)

        columns = ["Форма"] + table["columns"]
        tv["columns"] = columns
        for col in columns:
            tv.heading(col, text=col)
            tv.column(col, width=110, anchor="center")

        for row in table["rows"]:
            tv.insert("", "end", values=[row["form"]] + row["values"])

        tv.focus_set()       # чтобы Tab-ы не «улетали»

    # ────────────── назад в меню ──────────────
    def go_back(self):
        self.root.destroy()
        self.main_menu_root.deiconify()


# ─────────────────── самостоятельный запуск ───────────────────
if __name__ == "__main__":
    root = tb.Window(themename="minty")
    FormGuide(root, None)   # main_menu_root=None, потому что меню нет
    root.mainloop()
