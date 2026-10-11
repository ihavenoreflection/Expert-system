# main.py
from database import DatabaseManager
from logic import ExpertSystem
from gui import App

def main():
    # 1. Инициализация БД
    db = DatabaseManager()
    
    # 2. Инициализация логики
    expert = ExpertSystem(db)
    
    # 3. Запуск интерфейса
    app = App(db, expert)
    app.mainloop()

if __name__ == "__main__":
    main()