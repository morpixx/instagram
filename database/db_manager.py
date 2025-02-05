import sqlite3
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Account:
    email: str
    password: str
    registered: bool = False
    instagram_username: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_name: str = "instagram_accounts.db"):
        self.db_name = db_name
        self._init_database()

    def _init_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    email TEXT PRIMARY KEY,
                    password TEXT NOT NULL,
                    registered BOOLEAN DEFAULT FALSE,
                    instagram_username TEXT
                )
            """)
            conn.commit()

    def add_accounts(self, accounts_str: str) -> tuple[int, int]:
        """
        Додає акаунти у форматі email:password,email1:password1.
        Повертає кортеж (кількість доданих, кількість вже існуючих).
        """
        accounts_list = [acc.strip() for acc in accounts_str.split(',') if acc.strip()]
        added = 0
        existing = 0

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for account in accounts_list:
                try:
                    email, password = account.split(':')
                    cursor.execute(
                        "INSERT INTO accounts (email, password) VALUES (?, ?)",
                        (email.strip(), password.strip())
                    )
                    added += 1
                except sqlite3.IntegrityError:
                    existing += 1
                except ValueError:
                    # Якщо формат рядка невірний
                    print(f"Невірний формат для: {account}")
            conn.commit()
        return added, existing

    def get_unregistered_accounts(self) -> List[Account]:
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT email, password FROM accounts WHERE registered = FALSE"
            )
            rows = cursor.fetchall()
            return [Account(email, password) for email, password in rows]

    def update_account_status(self, email: str, instagram_username: str):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE accounts 
                   SET registered = TRUE, instagram_username = ? 
                   WHERE email = ?""",
                (instagram_username, email)
            )
            conn.commit()

    def clear_database(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts")
            conn.commit()
