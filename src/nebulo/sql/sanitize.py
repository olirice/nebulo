import secrets
import string


def secure_random_string(length=8) -> str:
    letters = string.ascii_lowercase
    return "".join([secrets.choice(letters) for _ in range(length)])


def sanitize(text: str) -> str:
    escape_key = secure_random_string()
    return f"${escape_key}${text}${escape_key}$"
