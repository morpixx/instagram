import concurrent.futures
from database.db_manager import DatabaseManager
from utils.proxy_handler import parse_proxy_string
from services.registration_worker import RegistrationWorker

class InstagramRegistrationSystem:
    def __init__(self):
        self.db = DatabaseManager()
        
    def display_menu(self):
        print("\n=== Instagram Registration System ===")
        print("1. Додати акаунти в базу даних")
        print("2. Почати реєстрацію")
        print("3. Очистити базу даних")
        print("4. Вихід")
        return input("Оберіть опцію: ")

    def handle_add_accounts(self):
        accounts = input("Введіть акаунти (email:password,email1:password1): ")
        added, existing = self.db.add_accounts(accounts)
        print(f"Успішно додано: {added}")
        print(f"Вже існують: {existing}")

    def handle_registration(self):
        accounts = self.db.get_unregistered_accounts()
        if not accounts:
            print("Немає незареєстрованих акаунтів. Будь ласка, додайте акаунти.")
            return

        # Отримуємо коректну відповідь для використання проксі
        use_proxy = None
        while use_proxy not in ['yes', 'no']:
            use_proxy = input("Використовувати проксі? (yes/no): ").strip().lower()
            if use_proxy not in ['yes', 'no']:
                print("Невірна опція. Спробуйте ще раз.")
        
        proxy = None
        if use_proxy == 'yes':
            print("Введіть деталі проксі (у форматі nsocks):")
            proxy_str = ""
            print("Введіть рядки (порожній рядок для завершення):")
            while True:
                line = input()
                if not line:
                    break
                proxy_str += line + "\n"
            proxy = parse_proxy_string(proxy_str)
            if not proxy:
                print("Невірний формат проксі.")
                return

        # Запитуємо кількість вікон незалежно від вибору проксі
        try:
            max_workers = int(input("Введіть кількість вікон (макс. 10): "))
            if max_workers > 10:
                max_workers = 10
        except ValueError:
            max_workers = 1

        # Виконуємо реєстрацію акаунтів (якщо proxy == None, то використовуємо звичайне з'єднання)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for account in accounts:
                worker = RegistrationWorker(account, proxy)
                futures.append(executor.submit(worker.register))
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    print(f"Успішно зареєстровано акаунт з username: {result}")
                else:
                    print("Реєстрація не вдалася для одного з акаунтів.")

    def handle_clear_database(self):
        confirm = input("Ви впевнені, що хочете очистити базу даних? (yes/no): ").strip().lower()
        if confirm == 'yes':
            self.db.clear_database()
            print("База даних очищена.")
        else:
            print("Операція скасована.")

    def run(self):
        while True:
            choice = self.display_menu()
            if choice == '1':
                self.handle_add_accounts()
            elif choice == '2':
                self.handle_registration()
            elif choice == '3':
                self.handle_clear_database()
            elif choice == '4':
                print("Вихід з програми.")
                break
            else:
                print("Невірна опція. Спробуйте ще раз.")

if __name__ == "__main__":
    system = InstagramRegistrationSystem()
    system.run()
