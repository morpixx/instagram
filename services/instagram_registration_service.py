from faker import Faker
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from typing import Optional
import calendar
import random
import time
import re

class InstagramRegistrationService:
    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 20)
        self.faker = Faker()

    def register_account(self, email: str, password: str) -> Optional[str]:
        """
        Виконує реєстрацію в Instagram:
         - заповнює email, повне ім'я, username, пароль
         - вводить дату народження
         - повертає згенерований username при успішній реєстрації,
           або None при помилці
        """
        try:
            self.driver.get("https://www.instagram.com/accounts/emailsignup/")
            time.sleep(2)  # Додамо затримку після відкриття сторінки

            # Приймаємо куки, якщо є
            try:
                cookie_button = self.wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow all cookies')]"))
                )
                cookie_button.click()
                time.sleep(1)  # Додатковий час для закриття банера
            except TimeoutException:
                pass

            # Вводимо email
            email_input = self.wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
            email_input.clear()
            email_input.send_keys(email)

            # Генеруємо повне ім'я (жіноче ім'я)
            full_name = self.faker.first_name_female() + " " + self.faker.last_name()
            name_input = self.driver.find_element(By.NAME, "fullName")
            name_input.clear()
            name_input.send_keys(full_name)

            # Генеруємо username
            base_username = re.sub(r'[^a-zA-Z0-9]', '', full_name.lower())  # Видаляємо пробіли і спецсимволи
            username = f"{base_username}{random.randint(1000, 9999)}"
            username_input = self.driver.find_element(By.NAME, "username")
            username_input.clear()
            username_input.send_keys(username)

            # Вводимо пароль
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.clear()
            password_input.send_keys(password)

            # Клікаємо "Next" (перехід до дати народження)
            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]")))
            next_button.click()
            time.sleep(3)  # Затримка для переходу до сторінки з датою народження

            # Вибір дати народження
            birth_month = Select(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@title='Month:']"))))
            birth_day = Select(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@title='Day:']"))))
            birth_year = Select(self.wait.until(EC.element_to_be_clickable((By.XPATH, "//select[@title='Year:']"))))

            # Генеруємо випадкову дату народження (від 18 до 30 років)
            year = random.randint(1994, 2006)
            month_index = random.randint(0, 11)  # Індекс місяця (0-11)
            day = random.randint(1, calendar.monthrange(year, month_index + 1)[1])  # Коректний день для місяця

            print(f"Вибрана дата народження: {day} {month_index + 1} {year}")

            # Встановлюємо значення в селектах
            birth_month.select_by_index(month_index)
            birth_day.select_by_value(str(day))
            birth_year.select_by_value(str(year))

            # Клікаємо "Next" (перехід до наступного етапу)
            next_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next')]")))
            next_button.click()

            return username

        except Exception as e:
            print(f"Instagram registration failed: {e}")
            return None
