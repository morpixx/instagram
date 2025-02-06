from dataclasses import dataclass
from typing import Optional, Dict
import re
import logging

logging.basicConfig(level=logging.ERROR)

@dataclass
class Proxy:
    host: str
    port: int
    username: str
    password: str

    def as_selenium_proxy(self) -> Dict[str, Dict[str, str]]:
        """Повертає проксі у форматі, який використовується для `undetected_chromedriver`."""
        return {
            'proxy': {
                'http': f'socks5://{self.username}:{self.password}@{self.host}:{self.port}',
                'https': f'socks5://{self.username}:{self.password}@{self.host}:{self.port}'
            }
        }

    def as_proxy_string(self, protocol: str = "socks5") -> str:
        """Повертає проксі у вигляді рядка, який можна передати як параметр `proxy` у SeleniumBase."""
        return f"{protocol}://{self.username}:{self.password}@{self.host}:{self.port}"

    def __repr__(self) -> str:
        return f"Proxy(host='{self.host}', port={self.port}, username='{self.username}', password='{self.password}')"


def parse_proxy_string(proxy_str: str) -> Optional[Proxy]:
    """
    Парсить проксі-рядок, підтримуючи чотири формати:
    1. Однорядковий: `45.135.232.137:24613:3c98c6:e9539f`
    2. Багаторядковий:
        IP: 45.135.232.137
        Port: 24613
        Username: 3c98c6
        Password: e9539f
    3. `TOKEN@IP:PORT`
    4. `login:password@hostname:port`
    """

    if not proxy_str or not isinstance(proxy_str, str):
        logging.error("[ПОМИЛКА] Порожній або неправильний формат проксі.")
        return None

    # 1. ОДНОРЯДКОВИЙ ФОРМАТ: IP:PORT:USERNAME:PASSWORD
    if re.match(r"^\d{1,3}(?:\.\d{1,3}){3}:\d{1,5}:[^:]+:[^:]+$", proxy_str):
        try:
            ip, port, username, password = proxy_str.split(":")
            return Proxy(ip, int(port), username, password)
        except ValueError as e:
            logging.error(f"[ПОМИЛКА] Не вдалося розібрати однорядковий проксі: {e}")
            return None

    # 2. НОВИЙ ФОРМАТ: login:password@hostname:port
    match = re.match(r"^([^:]+):([^@]+)@([^:]+):(\d{1,5})$", proxy_str)
    if match:
        username, password, host, port = match.groups()
        return Proxy(host, int(port), username, password)

    # 3. НОВИЙ ФОРМАТ: TOKEN@IP:PORT (де TOKEN = username, пароль відсутній)
    match = re.match(r"^([^@]+)@(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$", proxy_str)
    if match:
        username, ip, port = match.groups()
        return Proxy(ip, int(port), username, password="")

    # 4. БАГАТОРЯДКОВИЙ ФОРМАТ
    try:
        lines = [line.strip() for line in proxy_str.strip().split("\n") if line.strip()]

        ip = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("IP:")), None)
        port = next((int(line.split(": ", 1)[1].strip()) for line in lines if line.startswith("Port:")), None)
        username = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("Username:")), None)
        password = next((line.split(": ", 1)[1].strip() for line in lines if line.startswith("Password:")), None)

        if not ip or not port or not username or not password:
            logging.error("[ПОМИЛКА] Проксі містить неповні дані!")
            return None

        if not re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
            logging.error(f"[ПОМИЛКА] Невірний формат IP: {ip}")
            return None

        return Proxy(ip, port, username, password)

    except (ValueError, IndexError) as e:
        logging.error(f"[ПОМИЛКА] Не вдалося розібрати багаторядковий проксі: {e}")
        return None
