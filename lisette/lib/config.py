# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module for config loading helper functions"""
import argparse
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Callable

from lisette.lib import classes

log = logging.getLogger(__name__)


@dataclass
class Option:
    """A dataclass describing an option metadata"""

    name: str
    help: str
    choices: list[str] | None = None
    default: Any = None
    required: bool = False
    warning: bool = False
    post_load: Callable | None = None


def validate(option: Option, cfg: classes.Namespace) -> Any:
    """Validate an option and run it's post load, if any.

    If a default is set and it is missing, sets value to default. If a post_load
    function is set, run value through it and set to result. Then, return"""
    name = option.name
    if hasattr(cfg, name) and option.post_load is not None:
        cfg[name] = option.post_load(cfg[name])
    if hasattr(cfg, name):
        return
    if option.required:
        raise ValueError(f"Missing required option {option.name}")
    if option.warning:
        log.warning("Missing optional option '%s'", option.name)
    if option.default is not None:
        log.warning("Using default %s", option.default)
        cfg[name] = option.default
        if option.post_load is not None:
            cfg[name] = option.post_load(cfg[name])


def load_cli_args(options: list[Option]) -> classes.Namespace:
    """Load all options that are provided thru cli."""
    log.debug("Args %s", sys.argv)
    parser = argparse.ArgumentParser()
    for option in options:
        parser.add_argument("--" + option.name, help=option.help)
    cfg = classes.Namespace(**vars(parser.parse_args()))
    logging.debug("got cli args: %r", cfg)
    return cfg


def load_env_vars(options: list[Option], env_prefix) -> classes.Namespace:
    """Load all options set thru shell environment"""
    log.debug("Shell env: %s", os.environ)
    cfg = classes.Namespace()
    for option in options:
        env_name = option.name.upper()
        if env_prefix is not None:
            tmp = env_prefix, env_name
            env_name = "_".join(tmp)
        if env_name in os.environ:
            log.debug("found '%s': '%r' in environ", env_name, os.environ[env_name])
            cfg[option.name] = os.environ[env_name]
    return cfg


def finalize(
    options: list[Option], cli_args: classes.Namespace, env_vars: classes.Namespace
):
    """Join cli_args and env_vars and validate all options.

    For any options in both cli_args and env_vars, the value will be set to the
    one in cli args.

    Raises:
        ValueError: Missing required option
    """
    cfg = env_vars.union(cli_args)
    log.debug(cfg)
    for option in options:
        validate(option, cfg)
    return cfg
