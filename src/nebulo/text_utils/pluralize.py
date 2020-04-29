from functools import lru_cache

from inflect import engine


@lru_cache()
def get_pluralizer() -> engine:
    """Return an instance of inflection library's engine.
    This is wrapped in a function to reduce import side effects"""
    return engine()


@lru_cache()
def to_plural(text: str) -> str:
    pluralizer = get_pluralizer()
    return pluralizer.plural(text)
