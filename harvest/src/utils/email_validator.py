"""
Minimal email validator placeholder.
"""
import re


class EmailValidator:
    def is_valid(self, email: str) -> bool:
        return bool(re.match(r"[^@]+@[^@]+\\.[^@]+", email))
