import secrets
import string


def secure_random_string(length=8) -> str:
    letters = string.ascii_lowercase
    return "".join([secrets.choice(letters) for _ in range(length)])
