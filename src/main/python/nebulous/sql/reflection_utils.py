# pylint: disable=unused-argument
import re
import inflect


def to_camelcase(text):
    return str(
        text[0].lower() + re.sub(r"_([a-z])", lambda m: m.group(1).upper(), text[1:])
    )


def camelize_classname(base, tablename, table):
    "Produce a 'camelized' class name, e.g. "
    "'words_and_underscores' -> 'WordsAndUnderscores'"
    return to_camelcase(tablename)


_pluralizer = inflect.engine()


def pluralize_collection(base, local_cls, referred_cls, constraint):
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"

    referred_name = referred_cls.__name__
    pluralized = _pluralizer.plural(referred_name)
    return pluralized

def camelize_collection(base, local_cls, referred_cls, constraint):
    referred_name = referred_cls.__name__
    camel_name = to_camelcase(referred_name)
    return camel_name

def pluralize_and_camelize_collection(base, local_cls, referred_cls, constraint):
    "Produce an 'uncamelized', 'pluralized' class name, e.g. "
    "'SomeTerm' -> 'some_terms'"

    referred_name = referred_cls.__name__
    pluralized = _pluralizer.plural(referred_name)
    camel_name = to_camelcase(pluralized)
    return camel_name




