import re
from functools import lru_cache

__all__ = ["snake_to_camel"]

_re_snake_to_camel = re.compile(r"(_)([a-z\d])")


@lru_cache()
def snake_to_camel(s: str, upper: bool = True) -> str:
    """Convert from snake_case to CamelCase
    If upper is set, then convert to upper CamelCase, otherwise the first character
    keeps its case.
    """
    s = _re_snake_to_camel.sub(lambda m: m.group(2).upper(), s)
    if upper:
        s = s[:1].upper() + s[1:]
    return s
