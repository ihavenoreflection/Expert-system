# gui.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class App(tk.Tk):
    def __init__(self, db_manager, expert_system):
        super().__init__()
        self.db = db_manager
        self.expert = expert_system

        self.title("Экспертная система: Нобелевские лауреаты")
        self.geometry("650x450")

        self.current_question_id = None
        self.guess_made = False

        self.create_widgets()
        self.start_new_game()

    # ---------- Виджеты ----------
    def create_widgets(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Новая игра", command=self.start_new_game)
        filemenu.add_command(
            label="Добавить персонажа", command=self.add_character_dialog
        )
        filemenu.add_command(
            label="Добавить вопрос", command=self.add_question_dialog
        )
        filemenu.add_separator()
        filemenu.add_command(label="Выход", command=self.quit)
        menubar.add_cascade(label="Файл", menu=filemenu)
        self.config(menu=menubar)

        self.main_frame = ttk.Frame(self, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self.lbl_question = ttk.Label(
            self.main_frame,
            text="",
            font=("Arial", 14),
            wraplength=600,
            justify=tk.CENTER,
        )
        self.lbl_question.pack(pady=30)

        self.btn_frame = ttk.Frame(self.main_frame)
        self.btn_frame.pack(pady=10)

        self.btn_yes = ttk.Button(
            self.btn_frame, text="Да", command=lambda: self.answer(1), width=12
        )
        self.btn_yes.pack(side=tk.LEFT, padx=10)

        self.btn_no = ttk.Button(
            self.btn_frame, text="Нет", command=lambda: self.answer(0), width=12
        )
        self.btn_no.pack(side=tk.LEFT, padx=10)

        self.btn_dont_know = ttk.Button(
            self.btn_frame,
            text="Не знаю",
            command=lambda: self.answer(-1),
            width=12,
        )
        self.btn_dont_know.pack(side=tk.LEFT, padx=10)

        self.btn_guess = ttk.Button(
            self.main_frame, text="Попробовать угадать", command=self.force_guess
        )
        self.btn_guess.pack(pady=5)

        self.lbl_status = ttk.Label(
            self.main_frame, text="", font=("Arial", 9), foreground="gray"
        )
        self.lbl_status.pack(side=tk.BOTTOM, pady=10)

    # ---------- Игровой цикл ----------
    def start_new_game(self):
        self.expert.reset_game()
        self.guess_made = False
        self.enable_buttons()
        self.ask_next_question()

    def enable_buttons(self):
        self.btn_yes.config(state=tk.NORMAL)
        self.btn_no.config(state=tk.NORMAL)
        self.btn_dont_know.config(state=tk.NORMAL)
        self.btn_guess.config(state=tk.NORMAL)

    def disable_answer_buttons(self):
        self.btn_yes.config(state=tk.DISABLED)
        self.btn_no.config(state=tk.DISABLED)
        self.btn_dont_know.config(state=tk.DISABLED)

    def ask_next_question(self):
        if self.guess_made:
            return

        if self.expert.dont_know_count >= self.expert.dont_know_limit:
            self.btn_dont_know.config(state=tk.DISABLED)
        else:
            self.btn_dont_know.config(state=tk.NORMAL)

        best_name, prob = self.expert.get_best_guess()

        if prob > 0.85:
            self.finish_game(best_name, prob)
            return

        q_id = self.expert.get_best_question()
        if q_id is None:
            self.finish_game(best_name, prob)
            return

        self.current_question_id = q_id
        q_text = next(
            (q[1] for q in self.expert.questions if q[0] == q_id), ""
        )

        self.lbl_question.config(text=q_text)

        top = self.expert.get_top_candidates(3)
        top_str = ", ".join([f"{n}: {p*100:.0f}%" for n, p in top])
        self.lbl_status.config(
            text=f"Вопросов в запасе: {len(self.expert.available_q_ids)} | "
            f"'Не знаю': {self.expert.dont_know_count}/{self.expert.dont_know_limit}\n"
            f"Топ кандидатов: {top_str}"
        )

    def answer(self, ans):
        if self.current_question_id is None or self.guess_made:
            return

        self.expert.update_probabilities(self.current_question_id, ans)
        self.ask_next_question()

    def force_guess(self):
        if self.guess_made:
            return
        best_name, prob = self.expert.get_best_guess()
        self.finish_game(best_name, prob)

    def finish_game(self, name, prob):
        if self.guess_made:
            return
        self.guess_made = True
        self.disable_answer_buttons()
        self.btn_guess.config(state=tk.DISABLED)

        if name:
            msg = f"Я думаю, это {name}.\nУверенность: {prob*100:.1f}%"
        else:
            msg = "Я не могу угадать."

        response = messagebox.askyesno("Результат", msg + "\n\nЯ угадал?")
        if response:
            messagebox.showinfo("Победа", "Отлично! Я знаю всё!")
        else:
            messagebox.showinfo("Поражение", "Хм, попробуем в следующий раз.")

        self.start_new_game()

    # ---------- Добавление персонажа ----------
    def add_character_dialog(self):
        """Добавление персонажа с заполнением ответов на все вопросы (Да/Нет)."""
        name = simpledialog.askstring("Новый персонаж", "Введите имя персонажа:")
        if not name or not name.strip():
            return
        name = name.strip()

        if not self.db.add_character(name):
            messagebox.showerror("Ошибка", f"Персонаж «{name}» уже есть в базе.")
            return

        char_id = self.db.get_character_id_by_name(name)
        if char_id is None:
            messagebox.showerror("Ошибка", "Не удалось получить id персонажа.")
            return

        self._fill_answers_dialog(char_id, name)

        # Перезапускаем игру с учётом нового персонажа
        self.expert.reset_game()
        self.start_new_game()

    def _fill_answers_dialog(self, char_id, char_name):
        """Модальное окно: Да/Нет для каждого вопроса. Только 0 и 1."""
        questions = self.db.get_all_questions()

        dialog = tk.Toplevel(self)
        dialog.title(f"Ответы для «{char_name}»")
        dialog.geometry("650x550")
        dialog.transient(self)
        dialog.grab_set()

        header = ttk.Frame(dialog, padding=10)
        header.pack(fill="x")
        ttk.Label(
            header,
            text=f"Ответьте на вопросы про «{char_name}»",
            font=("Arial", 12, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Все ответы — только Да или Нет.",
            font=("Arial", 9),
            foreground="gray",
        ).pack(anchor="w")

        container = ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=canvas.yview
        )
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Шапка таблицы
        head = ttk.Frame(scroll_frame)
        head.pack(fill="x", pady=(0, 5))
        ttk.Label(head, text="№", width=4).pack(side="left")
        ttk.Label(head, text="Вопрос", width=50).pack(side="left")
        ttk.Label(head, text="Да", width=6).pack(side="left")
        ttk.Label(head, text="Нет", width=6).pack(side="left")

        vars_dict = {}
        for q_id, q_text in questions:
            row = ttk.Frame(scroll_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=str(q_id), width=4).pack(side="left")
            ttk.Label(row, text=q_text, width=50, anchor="w").pack(side="left")

            var = tk.IntVar(value=0)  # по умолчанию «Нет»
            vars_dict[q_id] = var

            ttk.Radiobutton(row, variable=var, value=1).pack(
                side="left", padx=(10, 0)
            )
            ttk.Radiobutton(row, variable=var, value=0).pack(
                side="left", padx=(20, 0)
            )

        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill="x", side="bottom")

        def save_and_close():
            for q_id, var in vars_dict.items():
                self.db.set_answer(char_id, q_id, var.get())
            messagebox.showinfo("Готово", f"Персонаж «{char_name}» сохранён.")
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        def cancel():
            if messagebox.askyesno(
                "Отмена",
                f"Удалить персонажа «{char_name}» из базы?",
            ):
                self.db.delete_character(char_id)
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        def fill_all_no():
            for v in vars_dict.values():
                v.set(0)

        def fill_all_yes():
            for v in vars_dict.values():
                v.set(1)

        ttk.Button(btn_frame, text="Отмена", command=cancel).pack(
            side="right", padx=5
        )
        ttk.Button(btn_frame, text="Сохранить", command=save_and_close).pack(
            side="right", padx=5
        )
        ttk.Button(btn_frame, text="Везде «Да»", command=fill_all_yes).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Везде «Нет»", command=fill_all_no).pack(
            side="left", padx=5
        )

    # ---------- Добавление вопроса ----------
    def add_question_dialog(self):
        """Добавление вопроса с заполнением ответов для каждого персонажа (Да/Нет)."""
        text = simpledialog.askstring("Новый вопрос", "Введите текст вопроса:")
        if not text or not text.strip():
            return
        text = text.strip()

        if not self.db.add_question(text):
            messagebox.showerror("Ошибка", f"Вопрос «{text}» уже есть в базе.")
            return

        q_id = self.db.get_question_id_by_text(text)
        if q_id is None:
            messagebox.showerror("Ошибка", "Не удалось получить id вопроса.")
            return

        self._fill_question_answers_dialog(q_id, text)

        # Перезапускаем игру с учётом нового вопроса
        self.expert.reset_game()
        self.start_new_game()


    def _fill_question_answers_dialog(self, q_id, q_text):
        """
        Модальное окно: для каждого персонажа — Да/Нет.
        Заполняет СТОЛБЕЦ матрицы (по одному ответу на каждого персонажа).
        """
        characters = self.db.get_all_characters()

        dialog = tk.Toplevel(self)
        dialog.title(f"Ответы на вопрос")
        dialog.geometry("650x550")
        dialog.transient(self)
        dialog.grab_set()

        header = ttk.Frame(dialog, padding=10)
        header.pack(fill="x")
        ttk.Label(
            header,
            text=f"Вопрос: «{q_text}»",
            font=("Arial", 12, "bold"),
            wraplength=620,
            justify="left",
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Отметьте для каждого персонажа — Да или Нет.",
            font=("Arial", 9),
            foreground="gray",
        ).pack(anchor="w")

        # Скроллируемая область
        container = ttk.Frame(dialog)
        container.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scroll_frame = ttk.Frame(canvas)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Шапка
        head = ttk.Frame(scroll_frame)
        head.pack(fill="x", pady=(0, 5))
        ttk.Label(head, text="№", width=4).pack(side="left")
        ttk.Label(head, text="Персонаж", width=35).pack(side="left")
        ttk.Label(head, text="Да", width=6).pack(side="left")
        ttk.Label(head, text="Нет", width=6).pack(side="left")

        vars_dict = {}
        for char_id, name in characters:
            row = ttk.Frame(scroll_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=str(char_id), width=4).pack(side="left")
            ttk.Label(row, text=name, width=35, anchor="w").pack(side="left")

            var = tk.IntVar(value=0)  # по умолчанию «Нет»
            vars_dict[char_id] = var

            ttk.Radiobutton(row, variable=var, value=1).pack(side="left", padx=(10, 0))
            ttk.Radiobutton(row, variable=var, value=0).pack(side="left", padx=(20, 0))

        # Кнопки внизу
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill="x", side="bottom")

        def save_and_close():
            for char_id, var in vars_dict.items():
                # Внимание: аргументы set_answer: (char_id, question_id, answer)
                self.db.set_answer(char_id, q_id, var.get())
            messagebox.showinfo("Готово", f"Ответы на вопрос «{q_text}» сохранены.")
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        def cancel():
            if messagebox.askyesno(
                "Отмена",
                f"Удалить вопрос «{q_text}» из базы?",
            ):
                self.db.delete_question(q_id)
            canvas.unbind_all("<MouseWheel>")
            dialog.destroy()

        def fill_all_no():
            for v in vars_dict.values():
                v.set(0)

        def fill_all_yes():
            for v in vars_dict.values():
                v.set(1)

        ttk.Button(btn_frame, text="Отмена", command=cancel).pack(
            side="right", padx=5
        )
        ttk.Button(btn_frame, text="Сохранить", command=save_and_close).pack(
            side="right", padx=5
        )
        ttk.Button(btn_frame, text="Везде «Да»", command=fill_all_yes).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Везде «Нет»", command=fill_all_no).pack(
            side="left", padx=5
        )