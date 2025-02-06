import undetected_chromedriver as uc
from typing import Optional
import time
import random
import os
import shutil

class BrowserManager:
    def __init__(self, proxy: Optional[dict] = None):
        self.proxy = proxy
        
    def create_browser(self) -> uc.Chrome:
        options = uc.ChromeOptions()
        options.add_argument('--start-maximized')  # Повноекранний режим
        options.add_argument('--lang=en-US')       # Англійська мова
        options.add_argument("--disable-blink-features=AutomationControlled")  # Маскує Selenium
        options.add_argument("--disable-infobars")  # Ховає інформаційні панелі Chrome
        options.add_argument("--disable-extensions")  # Вимикає розширення
        options.add_argument("--no-sandbox")  # Запуск без sandbox (може знадобитися на VPS)
        options.add_argument("--disable-dev-shm-usage")  # Для кращої стабільності

        # Якщо використовується проксі, встановлюємо його
        if self.proxy:
            options.add_argument(f'--proxy-server={self.proxy["proxy"]["https"]}')

        path = r"C:\Users\RomMan\appdata\roaming\undetected_chromedriver\undetected_chromedriver.exe"

        # Перевіряємо, чи існує вже undetected_chromedriver
        if not os.path.exists(path):
            # Копіюємо undetected_chromedriver в папку appdata
            shutil.copy("undetected_chromedriver.exe", path)

        driver = uc.Chrome(executable_path=path, options=options)

        # Маскування Selenium
        self._stealth_driver(driver)

        driver.maximize_window()
        return driver

    def _stealth_driver(self, driver):
        """Приховує Selenium та додає маскування браузера"""
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Приховування WebRTC (необхідно, якщо використовується проксі)
        driver.execute_script("""
            const getUserMedia = navigator.mediaDevices.getUserMedia;
            navigator.mediaDevices.getUserMedia = function (constraints) {
                return new Promise((resolve, reject) => {
                    if (constraints && constraints.video) {
                        reject(new Error('Not allowed'));
                    } else {
                        resolve(getUserMedia(constraints));
                    }
                });
            };
        """)
        
        # Виправлення navigator.languages (імітація реального браузера)
        driver.execute_script("""
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        """)

        # Виправлення navigator.plugins (порожній список = боту)
        driver.execute_script("""
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)

        # Додаємо випадкову затримку перед діями
        time.sleep(random.uniform(2, 5))

