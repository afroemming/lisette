# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Logging helper functions"""
import functools
import logging
import sys
from typing import Callable


def fallback_logger() -> logging.Logger:
    logging.basicConfig(level=logging.DEBUG)
    return logging.getLogger()


def initalize(cfg, pkg_name: str, debug=False):
    """Setup logging."""
    if debug:
        return fallback_logger()
    log_level: int = cfg.get("log_level")
    if not log_level:
        log_level = logging.WARNING
        logging.warning("Log level not configured. Using default WARNING")
    log: logging.Logger = logging.getLogger(pkg_name)
    log.setLevel(log_level)
    log.info("Using log level %r", logging.getLevelName(log_level))

    fmt: str = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt: str = "%b %d %H:%M:%S"
    formatter: logging.Formatter = logging.Formatter(fmt, datefmt)

    stream_handler: logging.Handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt=formatter)
    log.addHandler(stream_handler)

    return log


def get_numeric(txt: str) -> int:
    """Try to get numeric log level from txt, returning WARNING if invalid."""
    num = getattr(logging, txt, None)
    if num is None:
        logging.warning("Invalid log level %s. Using default WARNING.")
        return logging.WARNING
    return num


def logfn(fn: Callable):  # pylint: disable=C0103
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
