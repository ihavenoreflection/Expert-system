# database.py
import sqlite3


class DatabaseManager:
    def __init__(self, db_name="nobel_matrix.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.populate_initial_data()

    # ---------- Создание схемы ----------
    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                id   INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id   INTEGER PRIMARY KEY,
                text TEXT UNIQUE NOT NULL
            )
        """)
        # ВАЖНО: только 0 и 1 — никаких -1
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_matrix (
                char_id     INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer      INTEGER NOT NULL CHECK (answer IN (0, 1)),
                PRIMARY KEY (char_id, question_id),
                FOREIGN KEY (char_id)     REFERENCES characters(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id)  ON DELETE CASCADE
            )
        """)
        self.conn.commit()

    # ---------- Наполнение ----------
    def populate_initial_data(self):
        self.cursor.execute("SELECT count(*) FROM characters")
        if self.cursor.fetchone()[0] > 0:
            return  # база уже наполнена

        characters = [
            (1,  "Лев Толстой"),
            (2,  "Иван Бунин"),
            (3,  "Борис Пастернак"),
            (4,  "Михаил Шолохов"),
            (5,  "Александр Солженицын"),
            (6,  "Иосиф Бродский"),
            (7,  "Эрнест Хемингуэй"),
            (8,  "Габриэль Гарсиа Маркес"),
            (9,  "Редьярд Киплинг"),
            (10, "Джордж Бернард Шоу"),
            (11, "Томас Манн"),
            (12, "Герман Гессе"),
            (13, "Альбер Камю"),
            (14, "Сэмюэл Беккет"),
            (15, "Пабло Неруда"),
            (16, "Синклер Льюис"),
            (17, "Джон Голсуорси"),
            (18, "Уильям Фолкнер"),
            (19, "Франсуа Мориак"),
            (20, "Сельма Лагерлёф"),
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO characters (id, name) VALUES (?, ?)", characters
        )

        questions = [
            (1,  "Это женщина?"),
            (2,  "Он/Она из России/СССР?"),
            (3,  "Он/Она из США?"),
            (4,  "Он/Она из Европы?"),
            (5,  "Писал(а) на английском языке?"),
            (6,  "Был(а) репрессирован(а) или в изгнании?"),
            (7,  "Основной жанр — роман?"),
            (8,  "Получил(а) премию до 1950 года?"),
            (9,  "Он/Она из Латинской Америки?"),
            (10, "В творчестве есть философские мотивы?"),
            (11, "Был(а) военным корреспондентом?"),
            (12, "Он/Она из Азии или Африки?"),
            (13, "Умер(ла) до 1930 года?"),
            (14, "Получил(а) премию после 1960 года?"),
            (15, "Писал(а) преимущественно поэзию?"),
            (16, "Отказался(ась) от Нобелевской премии?"),
            (17, "Эмигрировал(а) на Запад?"),
            (18, "Писал(а) о войне или лагерях?"),
            (19, "Жил(а) в США после эмиграции?"),
            (20, "Творчество связано с Индией или колониями?"),
        ]
        self.cursor.executemany(
            "INSERT OR IGNORE INTO questions (id, text) VALUES (?, ?)", questions
        )
        self.conn.commit()
        self._fill_knowledge_matrix()

    def _fill_knowledge_matrix(self):
        """Только 1 (Да) и 0 (Нет)"""
        matrix = {
            1:  [0, 1, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # Толстой
            2:  [0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0],  # Бунин
            3:  [0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],  # Пастернак
            4:  [0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0],  # Шолохов
            5:  [0, 1, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 1, 1, 0],  # Солженицын
            6:  [0, 1, 1, 0, 1, 1, 0, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 0, 1, 0],  # Бродский
            7:  [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0],  # Хемингуэй
            8:  [0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # Маркес
            9:  [0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],  # Киплинг
            10: [0, 0, 0, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Шоу
            11: [0, 0, 1, 1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0],  # Манн
            12: [0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],  # Гессе
            13: [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Камю
            14: [0, 0, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],  # Беккет
            15: [0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],  # Неруда
            16: [0, 0, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # Льюис
            17: [0, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],  # Голсуорси
            18: [0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],  # Фолкнер
            19: [0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Мориак
            20: [1, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # Лагерлёф
        }

        rows = []
        for char_id, answers in matrix.items():
            if len(answers) != 20:
                raise ValueError(f"У персонажа {char_id} должно быть ровно 20 ответов")
            for q_id, ans in enumerate(answers, start=1):
                rows.append((char_id, q_id, ans))

        self.cursor.executemany(
            "INSERT OR IGNORE INTO knowledge_matrix (char_id, question_id, answer) "
            "VALUES (?, ?, ?)",
            rows,
        )
        self.conn.commit()

    # ---------- API ----------
    def get_all_characters(self):
        self.cursor.execute("SELECT id, name FROM characters ORDER BY id")
        return self.cursor.fetchall()

    def get_all_questions(self):
        self.cursor.execute("SELECT id, text FROM questions ORDER BY id")
        return self.cursor.fetchall()

    def get_answer(self, char_id, question_id):
        """Возвращает 1 или 0. Если записи нет — считаем 0 (безопасный дефолт)."""
        self.cursor.execute(
            "SELECT answer FROM knowledge_matrix WHERE char_id=? AND question_id=?",
            (char_id, question_id),
        )
        res = self.cursor.fetchone()
        return res[0] if res else 0

    def get_matrix_as_dict(self):
        """{(char_id, q_id): answer} — для logic.py"""
        self.cursor.execute(
            "SELECT char_id, question_id, answer FROM knowledge_matrix"
        )
        return {(c, q): a for c, q, a in self.cursor.fetchall()}

    # ---------- Добавление персонажа ----------
    def add_character(self, name):
        """
        Создаёт персонажа. Все ответы по умолчанию — 0 (Нет).
        Пользователь заполнит их через диалог.
        """
        try:
            self.cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM characters")
            new_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO characters (id, name) VALUES (?, ?)", (new_id, name)
            )
            self.cursor.execute("SELECT id FROM questions")
            q_ids = [row[0] for row in self.cursor.fetchall()]
            self.cursor.executemany(
                "INSERT INTO knowledge_matrix (char_id, question_id, answer) "
                "VALUES (?, ?, 0)",
                [(new_id, q) for q in q_ids],
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def set_answer(self, char_id, question_id, answer):
        """Устанавливает ответ в матрице (перезаписывает существующий). answer: 0 или 1."""
        if answer not in (0, 1):
            answer = 0
        self.cursor.execute(
            "INSERT OR REPLACE INTO knowledge_matrix "
            "(char_id, question_id, answer) VALUES (?, ?, ?)",
            (char_id, question_id, answer),
        )
        self.conn.commit()

    def get_character_id_by_name(self, name):
        self.cursor.execute("SELECT id FROM characters WHERE name = ?", (name,))
        res = self.cursor.fetchone()
        return res[0] if res else None

    def delete_character(self, char_id):
        """Удаляет персонажа и все его ответы."""
        self.cursor.execute("DELETE FROM characters WHERE id = ?", (char_id,))
        self.cursor.execute(
            "DELETE FROM knowledge_matrix WHERE char_id = ?", (char_id,)
        )
        self.conn.commit()

    # ---------- Добавление вопроса ----------
    def add_question(self, text):
        """
        Добавляет новый вопрос. По умолчанию все персонажи ответят на него
        «Нет» (0) — потом можно исправить вручную через SQL.
        """
        try:
            self.cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM questions")
            new_id = self.cursor.fetchone()[0]
            self.cursor.execute(
                "INSERT INTO questions (id, text) VALUES (?, ?)", (new_id, text)
            )
            self.cursor.execute("SELECT id FROM characters")
            c_ids = [row[0] for row in self.cursor.fetchall()]
            self.cursor.executemany(
                "INSERT INTO knowledge_matrix (char_id, question_id, answer) "
                "VALUES (?, ?, 0)",
                [(c, new_id) for c in c_ids],
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_question_id_by_text(self, text):
        self.cursor.execute("SELECT id FROM questions WHERE text = ?", (text,))
        res = self.cursor.fetchone()
        return res[0] if res else None

    def delete_question(self, question_id):
        """Удаляет вопрос и все связанные с ним ответы."""
        self.cursor.execute("DELETE FROM questions WHERE id = ?", (question_id,))
        self.cursor.execute(
            "DELETE FROM knowledge_matrix WHERE question_id = ?", (question_id,)
        )
        self.conn.commit()

    # ---------- Экспорт ----------
    def get_matrix_2d(self):
        self.cursor.execute("SELECT MAX(id) FROM characters")
        max_c = self.cursor.fetchone()[0] or 0
        self.cursor.execute("SELECT MAX(id) FROM questions")
        max_q = self.cursor.fetchone()[0] or 0

        matrix = [[0] * (max_q + 1) for _ in range(max_c + 1)]
        self.cursor.execute("SELECT char_id, question_id, answer FROM knowledge_matrix")
        for c, q, a in self.cursor.fetchall():
            matrix[c][q] = a
        return matrix