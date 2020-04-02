from typing import Callable


class ClassProperty(property):
    """Decorator to make a @classmethod accessible as a property"""

    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()


def classproperty(method: Callable):
    """Sets a method as a property
    Usage: @classproperty
    """
    return ClassProperty(classmethod(method))
