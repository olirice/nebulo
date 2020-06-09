
from sqlalchemy import Text, func, literal, literal_column

def literal_string(text):
    return literal_column(f"'{text}'")


