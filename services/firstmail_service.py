# services/firstmail_service.py
from seleniumbase import SB
import re
import time
from typing import Optional

class FirstMailService:
    def __init__(self):
        self.sb = None

    def initialize_sb(self):
        """Initialize SeleniumBase with required settings"""
        self.sb = SB(uc=True, test=True, locale_code="en")
        return self.sb

    def handle_captcha(self) -> bool:
        """Handle clickable captcha using SeleniumBase"""
        try:
            self.sb.uc_gui_click_captcha()
            self.sb.sleep(2)
            return True
        except Exception as e:
            print(f"[FIRSTMAIL] SeleniumBase failed to solve captcha: {e}")
            return False

    def get_verification_code(self, email: str, password: str) -> Optional[str]:
        """Get Instagram verification code from FirstMail"""
        try:
            with self.initialize_sb() as sb:
                url = "https://firstmail.ltd/en-US/webmail/login"
                sb.activate_cdp_mode(url)
                sb.get(url)
                
                # Login
                email_input = sb.find_element("#email")
                email_input.clear()
                email_input.send_keys(email)
                
                password_input = sb.find_element("#password")
                password_input.clear()
                password_input.send_keys(password)
                
                # Handle captcha if present
                try:
                    captcha = sb.find_element("#captcha")
                    if captcha and not self.handle_captcha():
                        return None
                except Exception:
                    pass
                
                # Click login and wait for inbox
                sb.find_element("button.btn-primary.w-100").click()
                sb.wait_for_element("li[data-target='inbox']", timeout=20)
                
                # Get verification code
                sb.find_element("li[data-target='inbox']").click()
                sb.sleep(2)
                
                email_item = sb.wait_for_element(
                    "//div[contains(@class, 'email-list-item-content') and contains(text(), 'is your Instagram code')]",
                    timeout=20,
                    by="xpath"
                )
                email_item.click()
                sb.sleep(2)
                
                code_element = sb.wait_for_element("td[style*='font-size:32px']", timeout=20)
                code_text = code_element.text.strip()
                
                match = re.search(r'\b\d{6}\b', code_text)
                return match.group() if match else None

        except Exception as e:
            print(f"[FIRSTMAIL] Failed to get Instagram code: {e}")
            return None