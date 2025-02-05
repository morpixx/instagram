from dataclasses import dataclass
from typing import Optional, Dict
import re

@dataclass
class Proxy:
    host: str
    port: int
    username: str
    password: str

    def as_selenium_proxy(self) -> Dict[str, Dict[str, str]]:
        """
        Повертає проксі у форматі, який використовується для `undetected_chromedriver`.
        """
        return {
            'proxy': {
                'http': f'socks5://{self.username}:{self.password}@{self.host}:{self.port}',
                'https': f'socks5://{self.username}:{self.password}@{self.host}:{self.port}'
            }
        }

    def as_proxy_string(self, protocol: str = "socks5") -> str:
        """
        Повертає проксі у вигляді рядка, який можна передати як параметр `proxy` у SeleniumBase.
        Дозволяє вибір протоколу (за замовчуванням `socks5`).
        """
        return f"{protocol}://{self.username}:{self.password}@{self.host}:{self.port}"

    def __repr__(self) -> str:
        return f"Proxy(host='{self.host}', port={self.port}, username='{self.username}', password='{self.password}')"


def parse_proxy_string(proxy_str: str) -> Optional[Proxy]:
    """
    Парсить проксі-рядок, підтримуючи два формати:
    1. Однорядковий: `45.135.232.137:24613:3c98c6:e9539f`
    2. Багаторядковий:
        Location: 🇺🇸 United States, Denver
        Ping: 108
        Speed: 7.006993 Mbps
        IP: 45.135.232.137
        Port: 24613
        Username: 3c98c6
        Password: e9539f
    """

    # Перевіряємо, чи не порожній вхідний рядок
    if not proxy_str or not isinstance(proxy_str, str):
        print("[ПОМИЛКА] Порожній або неправильний формат проксі.")
        return None

    # ОДНОРЯДКОВИЙ ФОРМАТ: IP:PORT:USERNAME:PASSWORD
    if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+:.+:.+$", proxy_str):
        try:
            parts = proxy_str.split(":")
            if len(parts) != 4:
                raise ValueError("Невірна кількість елементів в проксі.")
            
            ip, port, username, password = parts
            return Proxy(ip, int(port), username, password)
        except ValueError as e:
            print(f"[ПОМИЛКА] Не вдалося розібрати однорядковий проксі: {e}")
            return None

    # БАГАТОРЯДКОВИЙ ФОРМАТ
    try:
        lines = [line.strip() for line in proxy_str.strip().split("\n") if line.strip()]

        ip = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("IP:")), None)
        port = next((int(line.split(": ", 1)[1].strip()) for line in lines if line.startswith("Port:")), None)
        username = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("Username:")), None)
        password = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("Password:")), None)

        # Переконуємось, що всі необхідні дані присутні
        if not ip or not port or not username or not password:
            print("[ПОМИЛКА] Проксі містить неповні дані!")
            return None

        # Додаткова перевірка формату IP
        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
            print(f"[ПОМИЛКА] Невірний формат IP: {ip}")
            return None

        return Proxy(ip, port, username, password)

    except (ValueError, IndexError) as e:
        print(f"[ПОМИЛКА] Не вдалося розібрати багаторядковий проксі: {e}")
        return None
