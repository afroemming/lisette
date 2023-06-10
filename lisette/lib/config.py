# Copyright (c) 2023 Amelia Froemming
# SPDX-License-Identifier: MIT
"""Module for config loading helper functions"""
import argparse
import dataclasses
import logging
import os
import sys
import types
from typing import Any, Callable, Self

import dotenv

log = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Error for invalid configuration"""

    def __init__(self, *args: object) -> None:
        self.message = args[0]
        super().__init__(*args)


@dataclasses.dataclass
class Option:
    """Object representing an option.

    Arguments:
        name (str): Option name (long)
        flags (str): Other cli flags to use (Optional)
        arguments (dict): Dictionary of arguments to pass to argparse (Optional)
        post_load (Callable): Function to transform value with (Optional)
    """

    name: str
    flags: tuple[str, ...] = ()
    arguments: dict["str", Any] = dataclasses.field(default_factory=dict[str, Any])
    post_load: Callable[[Any], Any] | None = None
    required: bool = False


class Cfg(types.SimpleNamespace):
    """Holds a configuration"""

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)

    def set(self, key: str, val: Any) -> None:
        """Set value of key"""
        setattr(self, key, val)

    def get(self, key: Any, default: Any | None = None) -> Any:
        """Return value of attr key or default if not set"""
        return getattr(self, key, default)

    def merge(self, other: Self) -> Self:
        """Returns merged namespace of other with this object.

        This sets for all attrs in other self.attr to the value in other. Any
        attributes in both are overwritten by other.
        """
        for attr, val in vars(other).items():
            setattr(self, attr, val)
        return self

    def transform(self, options: list[Option]) -> None:
        """Applies transformations set in option.post_load to each member"""
        for option in options:
            if option.name in self and option.post_load is not None:
                val = self.get(option.name)
                self.set(option.name, option.post_load(val))

    @classmethod
    def from_argparse(cls, nspc: argparse.Namespace) -> Self:
        """Return Cfg made from an argparse.Namespace

        All attrs of nspc are put into a Cfg, then any that are None are deleted.
        """
        out = cls()
        for key, val in vars(nspc).items():
            if val is not None:
                out.set(key, val)
        return out


def get_cli_args(options: list[Option]) -> Cfg:
    """Return Cfg loaded with cli arguments"""
    parser = argparse.ArgumentParser(
        description="A Discord bot for making lists together."
    )
    for option in options:
        long_name: str = "--" + option.name.replace("_", "-")
        log.debug("making cli arg w/ flag '%s' from %s", long_name, option)
        parser.add_argument(*option.flags, long_name, **option.arguments)
    cli_args, _unknown = parser.parse_known_args()
    cfg = Cfg.from_argparse(cli_args)
    cfg.transform(options)
    return cfg


def get_env_vars(options: list[Option], env_prefix: str | None = None) -> Cfg:
    """Load env vars"""
    log.debug("Env: %s", os.environ)
    env_vars = Cfg()
    for option in options:
        env_name = option.name.upper()
        if env_prefix is not None:
            env_name = "_".join((env_prefix, env_name))
        log.debug("Trying to load %s", env_name)
        if env_name in os.environ:
            env_vars.set(option.name, os.environ[env_name])
            log.debug("got %s", env_vars.get(option.name))
        else:
            log.debug("%s not found in environment", option.name)
    env_vars.transform(options)
    return env_vars


def validate_required(options: list[Option], cfg: Cfg) -> None:
    """Raises ConfigurationError if cfg is missing a required option"""
    for option in options:
        log.debug("checking %s", option.name)
        if not option.required:
            log.debug("not required")
            continue
        if not option.name in cfg:
            raise ConfigurationError(f"Missing required setting {option.name}")


def get_cfg(
    options: list[Option], env_prefix: str | None = None, exit_on_error: bool=True
) -> Cfg:
    """Return a complete configuration from a list of options"""
    # load cli args first, so we can see if we are given an env file
    cli_args = get_cli_args(options)
    log.debug(": got %s", cli_args)
    if "env_file" in cli_args:
        log.info("loading env vars from %s", cli_args.env_file)
        dotenv.load_dotenv(cli_args.env_file, verbose=True)
    env_vars = get_env_vars(options, env_prefix)

    # Merge, overwritting dups by cli_args
    cfg: Cfg = env_vars.merge(cli_args)

    # Make sure required options are loaded
    try:
        log.debug("got cfg: %r", cfg)
        validate_required(options, cfg)
    except ConfigurationError as err:
        log.critical(err.message)
        if exit_on_error:
            log.critical("EXITING.")
            sys.exit(1)
        raise

    return cfg
