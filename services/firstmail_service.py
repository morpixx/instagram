import requests
import logging
import re
import urllib.parse
from typing import Optional
from database.db_manager import DatabaseManager
from os import getenv
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class InstagramVerificationService:
    def __init__(self, api_key: str, db_name: str = "instagram_accounts.db"):
        if not api_key:
            raise ValueError("API ключ не передано!")
        self.api_key = api_key
        self.db_manager = DatabaseManager(db_name)
        self.api_url = "https://api.firstmail.ltd/v1/market/get/message"

    def get_verification_code(self, email: str, password: str) -> Optional[str]:
        """
        Отримує код підтвердження для Instagram через API FirstMail (разова спроба).
        """
        headers = {
            "accept": "application/json",
            "X-API-KEY": self.api_key,
            "User-Agent": "Mozilla/5.0"
        }

        encoded_email = urllib.parse.quote(email)
        encoded_password = urllib.parse.quote(password)
        url = f"{self.api_url}?username={encoded_email}&password={encoded_password}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            
            if not response_data:
                logger.warning("Порожня відповідь від API.")
                return None
            
            logger.info(f"Отримана відповідь API: {response_data}")

            if response_data.get("has_message", False) and response_data.get("from") == "no-reply@mail.instagram.com":
                code = self._extract_code(response_data.get("subject", ""))
                if code:
                    return code
                else:
                    logger.warning("Код не вдалося витягнути з теми листа.")
            else:
                logger.warning("Код не знайдено або повідомлення не від Instagram.")
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP-помилка: {http_err} - {response.text}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Помилка запиту: {req_err}")
        except Exception as ex:
            logger.error(f"Несподівана помилка: {ex}")
        return None

    def _extract_code(self, subject: str) -> Optional[str]:
        """Виділяє 6-значний код з теми листа."""
        match = re.search(r'\b\d{6}\b', subject)
        return match.group() if match else None

    def process_accounts(self):
        """Обробляє акаунти у стані 'registering' для отримання кодів підтвердження."""
        accounts = self.db_manager.get_registering_accounts()
        for account in accounts:
            logger.info(f"Обробка акаунта: {account.email}")
            code = self.get_verification_code(account.email, account.password)
            if code:
                logger.info(f"Код підтвердження для {account.email}: {code}")
                self.db_manager.update_account_status(account.email, "verified")
            else:
                logger.warning(f"Не вдалося отримати код підтвердження для {account.email}")

if __name__ == "__main__":
    load_dotenv("api.env")
    api_key = getenv("FIRSTMAIL_API_KEY")
    if not api_key:
        raise ValueError("FIRSTMAIL_API_KEY не встановлено")
    
    logger.info(f"Запускаємо InstagramVerificationService з API ключем: {api_key}")
    service = InstagramVerificationService(api_key)
    service.process_accounts()
