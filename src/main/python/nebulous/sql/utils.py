from functools import lru_cache
from typing import Callable


class ClassProperty(property):
    """Decorator to make a @classmethod accessible as a property"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()  # pylint: disable=no-member


def classproperty(method: Callable):
    """Sets a method as a property
    Usage: @classproperty
    """
    return ClassProperty(classmethod(method))


def cachedclassproperty(method: Callable):
    """Caches a class property to be computed exactly once
    Uusage: @cachedclassproperty"""
    return classproperty(lru_cache()(method))
