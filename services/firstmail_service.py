import requests
from database.db_manager import DatabaseManager
from typing import Optional
from os import getenv
from dotenv import load_dotenv

class InstagramVerificationService:
    def __init__(self, api_key: str, db_name: str = "instagram_accounts.db"):
        self.api_key = api_key
        self.db_manager = DatabaseManager(db_name)
        self.api_url = "https://api.firstmail.ltd/v1/market/get/message"

    def get_verification_code(self, email: str, password: str) -> Optional[str]:
        """Отримує код підтвердження для Instagram через API FirstMail."""
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key
        }
        url = f"{self.api_url}?username={email}&password={password}"
        try:
            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get("has_message", False):
                message_subject = response_data.get("subject", "")
                message_body = response_data.get("message", "")
                if "ist dein Instagram-Code" in message_subject:
                    code = self._extract_code(message_body)
                    return code
            else:
                print(f"[ERROR] Failed to fetch messages: {response_data.get('message', 'Unknown error')}")
        except Exception as e:
            print(f"[ERROR] Exception occurred while fetching messages: {e}")
        return None

    def _extract_code(self, message_body: str) -> Optional[str]:
        """Виділяє код підтвердження з тексту повідомлення."""
        import re
        match = re.search(r'\b\d{6}\b', message_body)
        return match.group() if match else None

    def process_accounts(self):
        """Обробляє акаунти, які зараз реєструються, для отримання кодів підтвердження."""
        accounts = self.db_manager.get_registering_accounts()  # Змінено метод для обробки тільки активних реєстрацій
        for account in accounts:
            print(f"[INFO] Processing account: {account.email}")
            code = self.get_verification_code(account.email, account.password)
            if code:
                print(f"[SUCCESS] Verification code for {account.email}: {code}")
                # Оновлюємо статус акаунту
                self.db_manager.update_account_status(account.email, "verified")
            else:
                print(f"[WARNING] Failed to get verification code for {account.email}")

if __name__ == "__main__":
    
    load_dotenv()
    api_key = getenv('FIRSTMAIL_API_KEY')
    if not api_key:
        raise ValueError("FIRSTMAIL_API_KEY environment variable is not set")
    service = InstagramVerificationService(api_key)
    service.process_accounts()
