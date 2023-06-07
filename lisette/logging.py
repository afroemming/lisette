"""Logging helper functions"""
import logging
import functools
from typing import Callable


def get_numeric(txt: str) -> int:
    """Try to get numeric log level from txt, returning WARNING if invalid."""
    num = getattr(logging, txt, None)
    if num is None:
        logging.warning("Invalid log level %s. Using default WARNING.")
        return logging.WARNING
    return num


def logfn(fn: Callable):
    """Decorator that logs function calls when attached to a function fn"""

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if logging.root.level is not logging.DEBUG:
            return fn(*args, **kwargs)
        module = fn.__module__
        log = logging.getLogger(module)
        info = f"{fn}, args={args}, kwargs={kwargs}"
        log.debug("executing %s", info)
        out = fn(*args, *kwargs)
        log.debug("operation %s completed, returning %r", info, out)
        return out

    return wrapper
