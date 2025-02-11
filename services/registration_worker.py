# services/registration_worker.py

import time
import logging
from database.db_manager import Account, DatabaseManager
from services.browser_manager import BrowserManager
from services.instagram_registration_service import InstagramRegistrationService
from services.firstmail_service import InstagramVerificationService
from utils.proxy_handler import Proxy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class RegistrationWorker:
    """
    Клас-робітник для реєстрації одного акаунта.
    Для багатопотоковості кожен потік створює свій екземпляр цього класу із заданим акаунтом.
    """
    def __init__(self, account, proxy, api_key):
        self.account = account
        self.proxy = proxy
        self.api_key = api_key
        
        if not self.api_key:
            raise ValueError("API ключ не передано!")
        
        self.verification_service = InstagramVerificationService(api_key=self.api_key)

    def register(self) -> str:
        """
        Запускає процес реєстрації:
         - створює браузер (з проксі або без)
         - виконує реєстрацію в Instagram
         - отримує код підтвердження через API FirstMail
         - вводить код підтвердження в Instagram
         - оновлює статус акаунта в базі даних
         - повертає username, якщо успішно
        """
        instagram_username = None
        driver = None
        try:
            # Створення браузера із заданим проксі, якщо воно є
            browser_manager = BrowserManager(proxy=self.proxy.as_selenium_proxy() if self.proxy else None)
            driver = browser_manager.create_browser()
            if not driver:
                raise Exception("Failed to create browser")

            # Реєстрація в Instagram
            ig_service = InstagramRegistrationService(driver)
            instagram_username = ig_service.register_account(self.account.email, self.account.password)
            if not instagram_username:
                raise Exception("Instagram registration failed.")
            time.sleep(8)
            
            # Отримання коду підтвердження через API FirstMail для поточного акаунту
            verification_service = InstagramVerificationService(api_key=self.api_key)
            confirmation_code = verification_service.get_verification_code(self.account.email, self.account.password)
            if not confirmation_code:
                raise Exception("Failed to retrieve Instagram confirmation code.")

            # Введення коду підтвердження в Instagram за допомогою явних очікувань
            try:
                wait = WebDriverWait(driver, 20)
                verification_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
                verification_input.clear()
                verification_input.send_keys(confirmation_code)

                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Next')]")))
                next_button.click()

                # Очікуємо зміну URL або появу якогось елементу, що свідчить про успішну обробку коду
                wait.until(EC.url_changes(driver.current_url))
            except Exception as e:
                raise Exception(f"Failed to enter verification code in Instagram: {e}")

            # Оновлення статусу акаунта в базі даних
            db = DatabaseManager()
            db.update_account_status(self.account.email, instagram_username, registered=True, status="verified")

            logger.info(f"Account {self.account.email} successfully registered with username: {instagram_username}")
            return instagram_username
        except Exception as e:
            logger.error(f"RegistrationWorker error for {self.account.email}: {e}")
            return ""
        finally:
            if driver:
                driver.quit()
