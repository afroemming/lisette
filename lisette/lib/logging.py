# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Logging helper functions"""
import functools
import logging
import sys
from typing import Any, Callable, Final, Generic, ParamSpec, TypeVar

from lisette.lib import config

LEVELS: Final = {
    'DEBUG': 10,
    'INFO' : 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50 
}

def fallback_logger(name: str) -> logging.Logger:
    """Setup basic logger with log level DEBUG"""
    logging.basicConfig()
    fb_log = logging.getLogger(name)
    fb_log.setLevel(logging.DEBUG)
    return fb_log


def initalize(cfg: config.Cfg, pkg_name: str, debug: bool = False) -> logging.Logger:
    """Setup logging."""
    if debug:
        return fallback_logger(pkg_name)
    log_level: int = cfg.get("log_level")
    if not log_level:
        log_level = logging.WARNING
        logging.warning("Log level not configured. Using default WARNING")
    log: logging.Logger = logging.getLogger(pkg_name)
    log.setLevel(log_level)
    log.info("Using log level %r")

    fmt: str = "%(asctime)s - %(levelname)s - %(message)s"
    datefmt: str = "%b %d %H:%M:%S"
    formatter: logging.Formatter = logging.Formatter(fmt, datefmt)

    stream_handler: logging.Handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt=formatter)
    log.addHandler(stream_handler)

    return log

def get_numeric(txt: str) -> int:
    """Try to get numeric log level from txt, returning WARNING if invalid."""
    if txt in LEVELS:
        return LEVELS[txt]
    return logging.WARNING

P = ParamSpec('P')
R = TypeVar('R')

def logfn(f: Callable[P, R]) -> Callable[P, R]:
    @functools.wraps(f)
    def inner(*args: P.args, **kwargs: P.kwargs) -> R:
        logging.debug('called %s', f.__name__)
        return f(*args, **kwargs)
    return inner