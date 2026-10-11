# logic.py
import math


class ExpertSystem:
    def __init__(self, db_manager):
        self.db = db_manager
        self.reset_game()

    def reset_game(self):
        self.characters = self.db.get_all_characters()
        self.questions = self.db.get_all_questions()

        if not self.characters:
            self.probabilities = {}
        else:
            self.probabilities = {c[0]: 1.0 / len(self.characters) for c in self.characters}

        self.available_q_ids = [q[0] for q in self.questions]

        self.dont_know_limit = 2
        self.dont_know_count = 0

        # Загружаем всю матрицу ответов в память (быстро для 20×20)
        self.matrix = self.db.get_matrix_as_dict()

        # Вопросы, которые нужно задавать в первую очередь
        # (ключ — подстрока текста вопроса, значение — приоритет: чем выше, тем раньше)
        self.priority_patterns = [
            ("Это женщина?", 100),
            ("Отказался", 50),
            ("Индией или колониями", 40),
        ]

    # ---------- Получение ответа из матрицы ----------
    def _answer(self, char_id, q_id):
        return self.matrix.get((char_id, q_id), -1)

    # ---------- Выбор вопроса ----------
    def get_best_question(self):
        if not self.available_q_ids:
            return None

        # --- Шаг 1. Приоритетные вопросы ---
        for pattern, priority in self.priority_patterns:
            for q_id in self.available_q_ids:
                q_text = next((q[1] for q in self.questions if q[0] == q_id), "")
                if pattern.lower() in q_text.lower():
                    # Проверяем, что вопрос действительно разделяет кандидатов
                    if self._is_discriminating(q_id):
                        return q_id

        # --- Шаг 2. Обычный выбор по информационному выигрышу ---
        best_q_id = None
        best_score = -1.0

        for q_id in self.available_q_ids:
            # Пропускаем вопросы, которые не разделяют кандидатов
            if not self._is_discriminating(q_id):
                continue

            score = self._calculate_information_gain(q_id)
            if score > best_score:
                best_score = score
                best_q_id = q_id

        # Если ничего не нашли (все вопросы бесполезны) — вернём None
        if best_q_id is None:
            return None

        # Удаляем "мусорные" вопросы из доступных, чтобы не тормозили
        self._cleanup_useless_questions()

        return best_q_id

    def _is_discriminating(self, q_id):
        """
        Вопрос считается различающим, если среди кандидатов с ненулевой
        вероятностью есть хотя бы два с разными ответами.
        """
        answers = set()
        for char_id, prob in self.probabilities.items():
            if prob < 0.001:
                continue
            ans = self._answer(char_id, q_id)
            # -1 считаем как отдельный вариант (0.5)
            answers.add(ans)
            if len(answers) > 1:
                return True
        return False

    def _cleanup_useless_questions(self):
        """Убирает из available_q_ids вопросы, которые больше не различают кандидатов"""
        self.available_q_ids = [
            q_id for q_id in self.available_q_ids
            if self._is_discriminating(q_id)
        ]

    def _calculate_information_gain(self, q_id):
        """Информационный выигрыш от вопроса q_id (в битах)"""
        prob_yes = 0.0
        prob_no = 0.0

        for char_id, prob in self.probabilities.items():
            if prob < 0.001:
                continue
            db_ans = self._answer(char_id, q_id)
            if db_ans == 1:
                p_yes = 1.0
            elif db_ans == 0:
                p_yes = 0.0
            else:
                p_yes = 0.5
            prob_yes += p_yes * prob
            prob_no += (1.0 - p_yes) * prob

        # Энтропия до вопроса
        h_before = -sum(p * math.log2(p) for p in self.probabilities.values() if p > 0)

        # Энтропия после
        h_after = 0.0
        if prob_yes > 0.001:
            h_after += prob_yes * self._entropy_after_answer(q_id, 1)
        if prob_no > 0.001:
            h_after += prob_no * self._entropy_after_answer(q_id, 0)

        return h_before - h_after

    def _entropy_after_answer(self, q_id, user_answer):
        new_probs = []
        total = 0.0
        for char_id, prob in self.probabilities.items():
            if prob < 0.001:
                continue
            db_ans = self._answer(char_id, q_id)
            if db_ans == 1:
                p_b_given_a = 1.0
            elif db_ans == 0:
                p_b_given_a = 0.0
            else:
                p_b_given_a = 0.5

            p = p_b_given_a * prob if user_answer == 1 else (1.0 - p_b_given_a) * prob
            if p > 0:
                new_probs.append(p)
                total += p

        if total == 0:
            return 0.0

        entropy = 0.0
        for p in new_probs:
            p_norm = p / total
            entropy -= p_norm * math.log2(p_norm)
        return entropy

    # ---------- Обновление вероятностей ----------
    def update_probabilities(self, question_id, user_answer):
        if user_answer == -1:
            self.dont_know_count += 1
            if question_id in self.available_q_ids:
                self.available_q_ids.remove(question_id)
            return

        total_prob_event = 0.0
        for char_id, prob in self.probabilities.items():
            db_ans = self._answer(char_id, question_id)
            if db_ans == 1:
                p_b_given_a = 1.0
            elif db_ans == 0:
                p_b_given_a = 0.0
            else:
                p_b_given_a = 0.5

            p_contrib = p_b_given_a * prob if user_answer == 1 else (1.0 - p_b_given_a) * prob
            total_prob_event += p_contrib

        if total_prob_event == 0:
            if question_id in self.available_q_ids:
                self.available_q_ids.remove(question_id)
            return

        new_probabilities = {}
        for char_id, prob in self.probabilities.items():
            db_ans = self._answer(char_id, question_id)
            if db_ans == 1:
                p_b_given_a = 1.0
            elif db_ans == 0:
                p_b_given_a = 0.0
            else:
                p_b_given_a = 0.5

            p_contrib = p_b_given_a * prob if user_answer == 1 else (1.0 - p_b_given_a) * prob
            new_probabilities[char_id] = p_contrib / total_prob_event

        self.probabilities = new_probabilities

        if question_id in self.available_q_ids:
            self.available_q_ids.remove(question_id)

    # ---------- Угадывание ----------
    def get_best_guess(self):
        if not self.probabilities:
            return None, 0
        best_char_id = max(self.probabilities, key=self.probabilities.get)
        best_prob = self.probabilities[best_char_id]
        name = next((c[1] for c in self.characters if c[0] == best_char_id), "Неизвестно")
        return name, best_prob

    def get_top_candidates(self, n=3):
        sorted_probs = sorted(self.probabilities.items(), key=lambda x: -x[1])[:n]
        result = []
        for char_id, prob in sorted_probs:
            name = next((c[1] for c in self.characters if c[0] == char_id), "?")
            result.append((name, prob))
        return result