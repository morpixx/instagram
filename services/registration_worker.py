from database.db_manager import Account, DatabaseManager
from services.browser_manager import BrowserManager
from services.instagram_registration_service import InstagramRegistrationService
from services.firstmail_service import FirstMailService
from utils.proxy_handler import Proxy
from selenium.webdriver.common.by import By
import time

class RegistrationWorker:
    """
    Клас-робітник для реєстрації одного акаунта.
    """
    def __init__(self, account: Account, proxy: Proxy = None):
        self.account = account
        self.proxy = proxy

    def register(self) -> str:
        """
        Запускає процес реєстрації:
         - створює браузер (з проксі або без)
         - реєструє акаунт в Instagram
         - входить у FirstMail для отримання коду підтвердження
         - вводить код в Instagram
         - оновлює статус акаунта в базі даних
         - повертає username, якщо успішно
        """
        instagram_username = None
        driver = None
        try:
            browser_manager = BrowserManager(proxy=self.proxy.as_selenium_proxy() if self.proxy else None)
            driver = browser_manager.create_browser()
            
            # Добавляем проверку
            if not driver:
                raise Exception("Failed to create browser")
            
            # Реєстрація в Instagram
            ig_service = InstagramRegistrationService(driver)
            instagram_username = ig_service.register_account(self.account.email, self.account.password)
            if not instagram_username:
                raise Exception("Instagram registration failed.")
            
            # Затримка для отримання листа з FirstMail (може знадобитися повторна спроба)
            time.sleep(10)
            
            # Логін до FirstMail для отримання коду підтвердження
            firstmail_service = FirstMailService(driver)
            if not firstmail_service.login(self.account.email, self.account.password):
                raise Exception("FirstMail login failed.")
            
            confirmation_code = firstmail_service.get_instagram_code()
            if not confirmation_code:
                raise Exception("Failed to retrieve Instagram confirmation code.")
            
            # Введення коду підтвердження в Instagram
            try:
                verification_input = driver.find_element(By.NAME, "email_confirmation_code")
                verification_input.clear()
                verification_input.send_keys(confirmation_code)

                # Натискання кнопки "Next" після введення коду
                next_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Next')]")
                next_button.click()
                time.sleep(5)  # Чекаємо, щоб переконатися, що код введено успішно

            except Exception as e:
                raise Exception(f"Failed to enter verification code in Instagram: {e}")

            # Оновлюємо статус акаунта в базі даних
            db = DatabaseManager()
            db.update_account_status(self.account.email, instagram_username)
            
            return instagram_username
        except Exception as e:
            print(f"RegistrationWorker error for {self.account.email}: {e}")
            return ""
        finally:
            driver.quit()
